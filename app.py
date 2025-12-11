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

    # Prepare initial messages with full history
    messages = st.session_state.messages.copy()

    # Tools for RAG
    tools = [
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
    ]

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    with st.spinner("Thinking..."):
        content = ""
        while True:
            data = {
                "model": MODEL,
                "messages": messages,
                "tools": tools
            }
            response = requests.post(API_URL, headers=headers, json=data)
            if response.status_code != 200:
                st.error(f"API Error: {response.status_code} - {response.text}")
                st.error(f"Used Key (truncated for safety): {API_KEY[:20]}...{API_KEY[-20:]}")
                break

            api_resp = response.json()
            assistant_message = api_resp["choices"][0]["message"]
            messages.append(assistant_message)

            if "tool_calls" in assistant_message:
                for tool_call in assistant_message["tool_calls"]:
                    if tool_call["function"]["name"] == "collections_search":
                        # Placeholder for internal tool response (adjust if API provides results)
                        tool_args = json.loads(tool_call["function"]["arguments"])
                        tool_result = f"Retrieved results for query: {tool_args['query']} from collection."  # Simulate; replace if actual search needed
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_call["function"]["name"],
                            "content": tool_result
                        })
                # Continue loop for follow-up call
            else:
                content = assistant_message["content"]
                break

        if content:
            st.session_state.messages.append({"role": "assistant", "content": content})
            with st.chat_message("assistant"):
                st.markdown(content)
        else:
            st.error("No response generated—check logs for tool call issues.")
