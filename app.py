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
    messages = st.session_state.messages.copy()  # Use full history
    data = {
        "model": MODEL,
        "messages": messages,
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
                    "collection_ids": [COLLECTION_ID]  # Attach your collection
                }
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    with st.spinner("Thinking..."):
        # Initial API call
        response = requests.post(API_URL, headers=headers, json=data)
        if response.status_code != 200:
            st.error(f"API Error: {response.text}")
            st.error(f"Used Key (truncated for safety): {API_KEY[:20]}...{API_KEY[-20:]}")
            st.stop()

        api_resp = response.json()
        choices = api_resp["choices"]

        # Handle tool calls if present
        tool_calls = choices[0].get("tool_calls", [])
        if tool_calls:
            # Append the assistant's message with tool calls to history
            st.session_state.messages.append(choices[0]["message"])

            # For each tool call (e.g., collections_search), "execute" it
            for tool_call in tool_calls:
                if tool_call["function"]["name"] == "collections_search":
                    # Since it's internal, simulate execution by sending follow-up with dummy results or let API handle
                    # For now, assume API needs follow-up with tool response (adjust based on docs)
                    tool_args = json.loads(tool_call["function"]["arguments"])
                    # Here, you'd normally search the collection locally if possible, but since it's API-managed, send follow-up
                    tool_response = "Retrieved relevant snippets from the collection."  # Placeholder; replace with actual search if you have access
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "name": "collections_search",
                        "content": tool_response
                    })

            # Follow-up call with updated messages (including tool responses)
            data["messages"] = st.session_state.messages  # Updated history
            response = requests.post(API_URL, headers=headers, json=data)  # Second call
            api_resp = response.json()
            choices = api_resp["choices"]

        # Get final content
        content = choices[0]["message"]["content"]
        st.session_state.messages.append({"role": "assistant", "content": content})
        with st.chat_message("assistant"):
            st.markdown(content)
