import streamlit as st
import json
import asyncio
from xai_sdk import AsyncClient
from xai_sdk.chat import user
from xai_sdk.tools import collections_search
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

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

# Sync wrapper for async chat stream
def run_async_chat(prompt):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(async_chat(prompt))

@retry(
    stop=stop_after_attempt(5),  # Retry up to 5 times
    wait=wait_exponential(multiplier=1, min=5, max=60),  # Backoff: 5s, 10s, 20s, 40s, 60s
    retry=retry_if_exception_type(Exception),  # Retry on any exception (including timeout)
    reraise=True  # Re-raise the last exception if all retries fail
)
async def async_chat(prompt):
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

    full_response = ""
    async for response, chunk in chat.stream():
        if chunk.content:
            full_response += chunk.content
        # Handle tool calls if present
        for tool_call in chunk.tool_calls:
            st.info(f"Tool call: {tool_call.function.name} with args: {tool_call.function.arguments}")
            if tool_call.function.name == "collections_search":
                tool_args = json.loads(tool_call.function.arguments)
                tool_result = f"Retrieved results for query: {tool_args['query']} from collection."  
                chat.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": tool_result
                })

    return full_response

# User input
if prompt := st.chat_input("Enter your query (e.g., 'replace main wheel assembly procedure')"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.spinner("Thinking..."):
        content = run_async_chat(prompt)
        st.session_state.messages.append({"role": "assistant", "content": content})
        with st.chat_message("assistant"):
            st.markdown(content)
