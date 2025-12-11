# app.py - Simplified Streamlit app to test xAI collection access with multi-turn tool handling

import streamlit as st
import requests
import json

# Use Streamlit secrets for API key (add XAI_API_KEY in Streamlit settings)
API_KEY = st.secrets["XAI_API_KEY"]
MODEL = "grok-4"  # Or "grok-3" based on your subscription
COLLECTION_ID = "collection_04cfc2aa-4b9e-4187-82c4-6c8bbfa023a0"  # Your new collection ID

st.title("xAI Collection Test App")
st.markdown("This app tests accessing a collection with a test.txt file containing 'This is a Test'. Enter a query to test.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Enter your query (e.g., 'What is the content of the test file?')"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

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

    # Initial messages with full history
    messages = st.session_state.messages.copy()

    with st.spinner("Thinking..."):
        data = {
            "model": MODEL,
            "messages": messages,
            "tools": tools
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            api_resp = response.json()
            assistant_message = api_resp["choices"][0]["message"]
            content = assistant_message.get("content", "")
            st.session_state.messages.append({"role": "assistant", "content": content})
            with st.chat_message("assistant"):
                st.markdown(content)

            # Handle tool calls if present (multi-turn)
            if "tool_calls" in assistant_message:
                st.info("Tool calls detected - RAG is attempting to access the collection.")
                messages.append(assistant_message)
                for tool_call in assistant_message["tool_calls"]:
                    if tool_call["function"]["name"] == "collections_search":
                        tool_args = json.loads(tool_call["function"]["arguments"])
                        # Simulate tool result (in production, execute the search if external; for collections_search, placeholder as it's internal)
                        tool_result = f"Retrieved results for query: {tool_args['query']} from collection."  
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "name": tool_call["function"]["name"],
                            "content": tool_result
                        })
                # Follow-up call with tool result
                data["messages"] = messages
                data.pop("tools")  # Remove tools for follow-up as per docs
                response = requests.post(url, headers=headers, json=data)
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    st.session_state.messages.append({"role": "assistant", "content": content})
                    with st.chat_message("assistant"):
                        st.markdown(content)
                else:
                    st.error(f"Follow-up API Error: {response.text}")
        else:
            st.error(f"API Error: {response.text}")
