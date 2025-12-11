import streamlit as st
import requests
import json

# Use Streamlit secrets for API key
API_KEY = st.secrets["XAI_API_KEY"]
COLLECTION_ID = "aaebf3d1-e575-4eba-8966-db395919a1d5"  # Confirmed working format
MODEL = "grok-4"
API_URL = "https://api.x.ai/v1/chat/completions"

st.title("G450 AMT Assistant")
st.markdown("Ask maintenance queries about the Gulfstream G450. Powered by Grok with your uploaded manuals.")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Enter your query (e.g., 'replace main wheel assembly procedure')"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare initial payload with tools for RAG
    data = {
        "model": MODEL,
        "messages": st.session_state.messages,
        "tools": [
            {
                "type": "function",
                "function": {
                    "name": "collections_search",
                    "description": "Search the specified collections for relevant information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query"},
                            "limit": {"type": "integer", "description": "Number of results", "default": 10}
                        },
                        "required": ["query"]
                    },
                    "collection_ids": [COLLECTION_ID]
                }
            }
        ],
        "stream": true  # Enable streaming
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        tool_call = False

    with st.spinner("Thinking..."):
        response = requests.post(API_URL, headers=headers, json=data, stream=True)
        if response.status_code != 200:
            st.error(f"API Error: {response.text}")
            st.stop()

        # Process streaming response
        for chunk in response.iter_lines():
            if chunk:
                chunk_data = chunk.decode("utf-8")
                if chunk_data.startswith("data: "):
                    data_str = chunk_data[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_str)
                        choices = chunk_json["choices"]
                        if choices:
                            delta = choices[0]["delta"]
                            if "content" in delta and delta["content"]:
                                full_response += delta["content"]
                                message_placeholder.markdown(full_response + "▌")
                            if "tool_calls" in delta:
                                tool_call = True  # Flag if tool call is present
                    except json.JSONDecodeError:
                        st.error("Error parsing chunk")

        # Update final response
        if full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            message_placeholder.markdown(full_response)
        else:
            st.error("No content generated—check for tool calls or errors in logs.")

        if tool_call:
            st.info("Tool call detected—response may be incomplete. Try rephrasing the query.")
