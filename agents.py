import os
import time
from openai import OpenAI

class Agent:
    def __init__(self, name, instructions, vector_store_id):
        self.name = name
        self.instructions = instructions
        self.vector_store_id = vector_store_id
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        # Create an assistant with the file_search tool and your vector store ID
        self.assistant = self.client.beta.assistants.create(
            name=self.name,
            instructions=self.instructions,
            model="gpt-4o",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [self.vector_store_id]
                }
            }
        )

    def run(self, prompt):
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

        # Poll until the run completes
        while run.status in ["queued", "in_progress"]:
            time.sleep(1)
            run = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        # Retrieve messages from the thread
        messages = self.client.beta.threads.messages.list(thread_id=thread.id)

        # Extract and return the assistant's response
        for message in messages.data:
            if message.role == "assistant":
                return message.content[0].text.value

        return "No response from assistant."


# Example usage:
if __name__ == "__main__":
    VECTOR_STORE_ID = os.environ.get("VECTOR_STORE_ID")
    if not VECTOR_STORE_ID:
        raise ValueError("Please set VECTOR_STORE_ID environment variable.")

    agent = Agent(
        name="Documentation Helper",
        instructions="You are a helpful AI expert that can search through documentation tools information.",
        vector_store_id=VECTOR_STORE_ID,
    )

    question = "What are components for AI agent?"
    answer = agent.run(question)
    print("Assistant answer:", answer)
