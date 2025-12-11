import streamlit as st
import requests
import json

# Use Streamlit secrets for API key
API_KEY = st.secrets["XAI_API_KEY"]
COLLECTION_ID = "aaebf3d1-e575-4eba-8966-db395919a1d5"  # Confirmed working format
MODEL = "grok-4"  # Or "grok-3" based on your subscription

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

    # API call to Grok (fallback without tools)
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "collection_id": COLLECTION_ID  # Attach if supported; may trigger basic RAG
    }

    with st.spinner("Thinking..."):
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"]
            st.session_state.messages.append({"role": "assistant", "content": content})
            with st.chat_message("assistant"):
                st.markdown(content)
        else:
            st.error(f"API Error: {response.text}")
            st.error(f"Used Key (truncated for safety): {API_KEY[:20]}...{API_KEY[-20:]}")
