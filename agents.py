import os
import time
import json
import requests
from openai import OpenAI

class Agent:
    def __init__(self, name, instructions, vector_store_id, enable_web_search=False):
        self.name = name
        self.instructions = instructions
        self.vector_store_id = vector_store_id
        self.enable_web_search = enable_web_search
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        # Build tools list
        tools = [{"type": "file_search"}]
        
        if enable_web_search:
            tools.append({"type": "function", "function": self._get_web_search_function()})

        # Create an assistant with the specified tools
        self.assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions=self.instructions,
            model="gpt-4o",
            tools=tools,
            tool_resources={
                "file_search": {
                    "vector_store_ids": [self.vector_store_id]
                }
            }
        )

    def _get_web_search_function(self):
        """Define the web search function schema for OpenAI"""
        return {
            "name": "web_search",
            "description": "Search the web for current information using a search query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find information on the web"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of search results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }

    def _perform_web_search(self, query, num_results=5):
        """
        Perform web search using Bing Search API
        """
        try:
            search_url = "https://api.bing.microsoft.com/v7.0/search"
            subscription_key = os.environ.get("BING_SEARCH_KEY")
            
            if not subscription_key:
                return {"error": "BING_SEARCH_KEY not configured in environment variables"}
            
            headers = {"Ocp-Apim-Subscription-Key": subscription_key}
            params = {
                "q": query, 
                "count": min(num_results, 10),  # Limit to 10 max
                "textDecorations": False, 
                "textFormat": "Raw"
            }
            
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            search_results = response.json()
            
            # Format results for the assistant
            formatted_results = []
            if "webPages" in search_results and "value" in search_results["webPages"]:
                for result in search_results["webPages"]["value"]:
                    formatted_results.append({
                        "title": result.get("name", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", "")
                    })
            
            return {
                "query": query,
                "results": formatted_results,
                "total_results": len(formatted_results)
            }
            
        except requests.exceptions.Timeout:
            return {"error": "Search request timed out"}
        except requests.exceptions.RequestException as e:
            return {"error": f"Search request failed: {str(e)}"}
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

    def _handle_function_calls(self, run, thread_id):
        """Handle function calls during assistant execution"""
        tool_outputs = []
        
        if run.required_action and run.required_action.submit_tool_outputs:
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                if tool_call.function.name == "web_search":
                    try:
                        # Parse arguments
                        args = json.loads(tool_call.function.arguments)
                        query = args.get("query", "")
                        num_results = args.get("num_results", 5)
                        
                        # Perform web search
                        search_result = self._perform_web_search(query, num_results)
                        
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(search_result)
                        })
                    except Exception as e:
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"error": f"Failed to process search: {str(e)}"})
                        })
        
        if tool_outputs:
            # Submit tool outputs
            run = self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
        
        return run

    def run(self, prompt):
        try:
            # Create a thread
            thread = self.client.beta.threads.create()

            # Add the user's message to the thread
            self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt
            )

            # Run the assistant on the thread
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant.id
            )

            # Poll until the run completes, handling function calls
            max_iterations = 10  # Prevent infinite loops
            iteration = 0
            
            while run.status in ["queued", "in_progress", "requires_action"] and iteration < max_iterations:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                
                # Handle function calls if required
                if run.status == "requires_action":
                    run = self._handle_function_calls(run, thread.id)
                
                iteration += 1

            # Check for timeout or failure
            if iteration >= max_iterations:
                return "Request timed out. Please try again with a simpler question."
                
            if run.status == "failed":
                return "Sorry, I encountered an error processing your request. Please try again."

            # Retrieve messages from the thread
            messages = self.client.beta.threads.messages.list(thread_id=thread.id)

            # Extract and return the assistant's response
            return self._format_response(messages.data)
            
        except Exception as e:
            return f"Error: {str(e)}"

    def _format_response(self, messages):
        """
        Extract and format the assistant's response from messages.
        """
        # Look through messages starting from the most recent
        for message in reversed(messages):
            if message.role == "assistant":
                if message.content and len(message.content) > 0:
                    # Handle different content types
                    formatted_content = []
                    
                    for content_item in message.content:
                        if hasattr(content_item, 'text') and content_item.text:
                            # Extract text content
                            text_content = content_item.text.value
                            
                            # Clean up the text
                            text_content = self._clean_text(text_content)
                            formatted_content.append(text_content)
                        
                        elif hasattr(content_item, 'type'):
                            # Handle other content types
                            formatted_content.append(f"[{content_item.type.upper()} content]")
                    
                    if formatted_content:
                        return "\n\n".join(formatted_content)
        
        return "No response from assistant."

    def _clean_text(self, text):
        """
        Clean and format the response text for better readability.
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Ensure proper spacing after periods
        text = text.replace(". ", ".\n\n")
        
        # Handle bullet points and lists better
        text = text.replace("• ", "\n• ")
        text = text.replace("- ", "\n- ")
        
        # Handle numbered lists
        import re
        text = re.sub(r'(\d+\.) ', r'\n\1 ', text)
        
        # Remove multiple consecutive newlines but preserve intentional formatting
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text


# Example usage:
if __name__ == "__main__":
    VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID")
    if not VECTOR_STORE_ID:
        raise ValueError("Please set VECTOR_STORE_ID environment variable.")

    # Create agent with file search only
    file_agent = Agent(
        name="Documentation Helper",
        instructions="You are a helpful AI expert that can search through documentation.",
        vector_store_id=VECTOR_STORE_ID,
        enable_web_search=False
    )

    # Create agent with both file search and web search
    web_agent = Agent(
        name="Research Assistant",
        instructions="You are a helpful AI expert that can search through documentation and the web.",
        vector_store_id=VECTOR_STORE_ID,
        enable_web_search=True
    )

    question = "What are components for AI agent?"
    
    print("File search only:")
    answer = file_agent.run(question)
    print("Answer:", answer)
    
    print("\nWith web search:")
    answer = web_agent.run(question)
    print("Answer:", answer)