import streamlit as st
import os
from agents import Agent
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Ensure your OpenAI key is available from .env file
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
VECTOR_STORE_ID = os.environ["VECTOR_STORE_ID"]

# Initialize session state for chat history if it doesn't exist
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize search tool preferences if they don't exist
if "use_web_search" not in st.session_state:
    st.session_state.use_web_search = True
if "use_file_search" not in st.session_state:
    st.session_state.use_file_search = True

# Function to create agent with selected tools
def create_research_assistant():
    return Agent(
        name="Research Assistant",
        instructions="""You are a research assistant who searches the web and responds to questions based on the documents provided to you. 
        
        Always cite your sources when responding to questions. Maintain the conversation context and refer to previous exchanges when appropriate.
        If you don't have enough information to answer a question, say so and suggest what additional information might help.
        
        Format your responses in a clear, readable manner using markdown formatting when appropriate.
        """,
        vector_store_id=VECTOR_STORE_ID,
        enable_web_search=st.session_state.use_web_search
    )

# Function to get research response
def get_research_response(question, history):
    # Create agent with current tool selections
    research_assistant = create_research_assistant()
    
    # Combine history and current question to provide context
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    prompt = f"Context of our conversation:\n{context}\n\nCurrent question: {question}"
    
    return research_assistant.run(prompt)

# Streamlit UI
st.set_page_config(page_title="Research Assistant", layout="wide")
st.title("🔍 Research Assistant")
st.write("Ask me anything, and I'll search for information to help answer your questions.")

# Sidebar controls for search tool selection
st.sidebar.title("Search Settings")

# Tool selection toggles
st.sidebar.subheader("Select Search Sources")
web_search = st.sidebar.checkbox("Web Search", value=st.session_state.use_web_search, key="web_search_toggle")
file_search = st.sidebar.checkbox("Vector Store Search", value=st.session_state.use_file_search, key="file_search_toggle")

# Update session state when toggles change
if web_search != st.session_state.use_web_search:
    st.session_state.use_web_search = web_search
    
if file_search != st.session_state.use_file_search:
    st.session_state.use_file_search = file_search

# Validate that at least one search source is selected
if not st.session_state.use_web_search and not st.session_state.use_file_search:
    st.sidebar.warning("Please select at least one search source")

# Conversation controls
st.sidebar.subheader("Conversation")
if st.sidebar.button("Clear Conversation"):
    st.session_state.messages = []
    st.rerun()

# Display some helpful examples
with st.sidebar.expander("Example Questions"):
    st.markdown("""
    - What are the key findings in my vector store documents?
    - Find the latest research on AI Agents.
    - Summarize the information about "TOPIC" from my documents.
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made by Rendani")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
user_question = st.chat_input("Ask your research question")

if user_question:
    # Check if at least one search source is selected
    if not st.session_state.use_web_search and not st.session_state.use_file_search:
        st.error("Please select at least one search source in the sidebar")
    else:
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_question)
        
        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Researching..."):
                try:
                    response = get_research_response(user_question, st.session_state.messages)
                    st.markdown(response)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})