from crewai import Agent, Task, Crew, LLM
from langchain_community.tools.tavily_search import TavilySearchResults
from crewai.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()
from langchain_tavily import TavilySearch

s_tool = TavilySearch()


@tool
def tavily_search(query: str):
    """Searches the web for answers according to user's query"""
    return s_tool.run(query)

# ✅ LLM (Gemini API Key)
key = os.getenv('GEMINI_API_KEY')
llm = LLM(model="gemini/gemini-2.0-flash", api_key=key)

# ✅ Conversation memory
chat_memory = []


def qna_agent(user_input: str):
    """Tool that wraps a Crew to answer user queries."""

    context = "\n".join([f"User: {q}\nAssistant: {a}" for q, a in chat_memory[-5:]])

    agent1 = Agent(
        llm=llm,
        tools=[tavily_search],  # type: ignore
        backstory=(
            "You are a helpful assistant who can answer questions using your knowledge. "
            "When you don't know something, you search the web for accurate information. "
            "Always provide the sources of your information if you use search."
        ),
        role="QnA Assistant",
        goal="Answer the query of the user accurately. Use the search tool ONLY when needed, and when search is used, include sources."
    )

    qna_task = Task(
        agent=agent1,
        description=f"""{context}
        Answer this user question: {user_input}            
        Instructions:
        1. First try to answer from your knowledge
        2. For context-related queries, use context 
        3. If you need more information, use the search tool
        4. Provide a clear, helpful answer
        5. Remember this conversation for context""",
        expected_output="A clear, helpful answer to the user's question"
    )

    crew = Crew(
        agents=[agent1],
        tasks=[qna_task],
        verbose=True,
        memory=False,
    )

    response = crew.kickoff()
    chat_memory.append((user_input, response))
    return response
