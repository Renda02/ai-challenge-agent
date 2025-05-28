# AI research assistant

A research assistant that combines web search and document analysis to answer questions and provide comprehensive information.

## Purpose

This assistant operates in a general research domain. It searches through uploaded documents and web sources to provide accurate, cited responses to user questions.

## Tools

The assistant uses 2 external data sources:

- **Bing Search API**: Searches current web information and returns relevant results with titles, URLs, and snippets
- **OpenAI Vector Store**: Searches through uploaded documents using file search capabilities

## Memory types

This research AI agent uses 3 types of memory to track information effectively:

**Short-term memory**
The agent maintains conversation context within each session. It references previous exchanges and builds on earlier questions and answers.

Example: When you ask a follow-up question about a topic discussed earlier, the agent remembers the context and provides relevant responses.

**Long-term memory**
The agent stores documents in a vector store that persists across sessions. This creates a knowledge base that grows over time.

Example: Documents you upload today remain available for future conversations, letting the agent reference previously analyzed information.

**Semantic memory**
The agent understands relationships between concepts and can connect information from different sources.

Example: When you ask about "AI agents," the agent can link information from web search results with relevant sections from your uploaded documents to provide comprehensive answers.

## How to use

1. Set your environment variables in a `.env` file:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `VECTOR_STORE_ID`: Your vector store ID
   - `BING_SEARCH_KEY`: Your Bing Search API key

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   streamlit run app.py
   ```

4. Use the sidebar to enable or disable search sources
5. Ask questions in the chat interface
6. The assistant searches both web and document sources to provide comprehensive answers

## Features

- Real-time web search integration
- Document analysis and citation
- Conversation history tracking
- Configurable search sources
- Clean, formatted responses with markdown support

The assistant maintains context throughout conversations and cites sources when providing information.