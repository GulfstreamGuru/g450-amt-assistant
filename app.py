import streamlit as st
import os
from xai_sdk import AsyncClient
from xai_sdk.chat import user
from xai_sdk.tools import collections_search

# Use Streamlit secrets for API key
API_KEY = st.secrets["XAI_API_KEY"]
COLLECTION_ID = "aaebf3d1-e575-4eba-8966-db395919a1d5"  # Confirmed working format
MODEL = "grok-4"

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

    client = AsyncClient(api_key=API_KEY)

    # Create chat with collections_search tool
    chat = client.chat.create(
        model=MODEL,
        tools=[
            collections_search(collection_ids=[COLLECTION_ID]),
        ],
    )

    # Append the user prompt to the chat
    chat.append(user(prompt))

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

    with st.spinner("Thinking..."):
        async for response, chunk in chat.stream():
            if chunk.content:
                full_response += chunk.content
                message_placeholder.markdown(full_response + "▌")

            # Handle tool calls if present (for debugging)
            for tool_call in chunk.tool_calls:
                st.info(f"Tool call: {tool_call.function.name} with args: {tool_call.function.arguments}")

        if full_response:
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            message_placeholder.markdown(full_response)
        else:
            st.error("No response generated—check for errors in logs.")
