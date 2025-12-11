# app.py - Simple Streamlit app to test xAI collection access

import streamlit as st
import requests
import json

# Use Streamlit secrets for API key (add XAI_API_KEY in Streamlit settings)
API_KEY = st.secrets["XAI_API_KEY"]
MODEL = "grok-4"  # Or "grok-3" based on your subscription
COLLECTION_ID = "collection_04cfc2aa-4b9e-4187-82c4-6c8bbfa023a0"  # Replace with your actual collection ID (e.g., aaebf3d1-e575-4eba-8966-db395919a1d5)

st.title("xAI Collection Test App")
st.markdown("This app tests accessing a collection with a test.txt file containing 'This is a Test'.")

# Test query
test_query = "What is the content of the test file in the collection?"

if st.button("Run Test Query"):
    with st.spinner("Querying Grok with collection..."):
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": MODEL,
            "messages": [{"role": "user", "content": test_query}],
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
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            api_resp = response.json()
            content = api_resp["choices"][0]["message"]["content"]
            st.success("Response from Grok:")
            st.markdown(content)
            if "tool_calls" in api_resp["choices"][0]["message"]:
                st.info("Tool calls detected - RAG is attempting to access the collection.")
        else:
            st.error(f"API Error: {response.text}")
