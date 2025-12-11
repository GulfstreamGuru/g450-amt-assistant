import streamlit as st
import json
import asyncio
from xai_sdk import AsyncClient
from xai_sdk.chat import user, tool_result
from xai_sdk.tools import collections_search

# Use Streamlit secrets for API key
API_KEY = st.secrets["XAI_API_KEY"]
COLLECTION_ID = "aaebf3d1-e575-4eba-8966-db395919a1d5"  # Confirmed working format
MODEL = "grok-4"
TIMEOUT = 120  # Increased to 2 minutes for MCP listing

st.title("G450 AMT Assistant")
st.markdown("Ask maintenance queries about the Gulfstream G450. Powered by Grok with your uploaded manuals.")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Sync wrapper for async chat stream
def run_async_chat(prompt):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_chat(prompt))
    except asyncio.TimeoutError:
        return "Timeout error during tool listing—please try again or rephrase the query."

async def async_chat(prompt):
    client = AsyncClient(api_key=API_KEY)

    # Create chat with collections_search tool
    chat = client.chat.create(
        model=MODEL,
        tools=[
            collections_search(collection_ids=[COLLECTION_ID]),
        ],
    )

    # Append the user
