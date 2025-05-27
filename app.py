import streamlit as st
import os
from agents import Agent
from dotenv import load_dotenv

load_dotenv(override=True)

VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID")
if not VECTOR_STORE_ID:
    st.error("VECTOR_STORE_ID not set in environment variables.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🔍 Research Assistant (File Search only)")

def get_research_response(question, history):
    instructions = """You are a helpful AI expert that can search through documentation tools information."""
    agent = Agent(
        name="Documentation Helper",
        instructions=instructions,
        vector_store_id=VECTOR_STORE_ID
    )
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    prompt = f"Context of our conversation:\n{context}\n\nCurrent question: {question}"
    return agent.run(prompt)

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_question = st.chat_input("Ask your research question")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Researching..."):
            answer = get_research_response(user_question, st.session_state.messages)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
