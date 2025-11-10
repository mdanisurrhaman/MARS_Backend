from crewai import Agent,Task,Crew,LLM
from langchain_tavily import TavilySearch
from crewai.tools import tool
from dotenv import load_dotenv
load_dotenv()
import os
import requests  

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

s_tool = TavilySearch()

@tool
def tavily_search(query:str):
    "Searches the web for answers according to user's query"
    search = s_tool.run(query)
    return search   

key=os.getenv('GEMINI_API_KEY')
llm = LLM(model= "gemini/gemini-2.0-flash", api_key=key)

chat_memory = []

@tool
def qna_agent(user_input:str):
    "Tool that wraps a Crew to answer user queries."
    
    
    context = "\n".join([f"User: {q}\n  Assistant: {a}" for q, a in chat_memory[-5:]])   
    agent1 = Agent(llm=llm,
        tools=[tavily_search,], #type:ignore
        backstory="""You are a helpful assistant who can answer questions using 
        your knowledge. When you don't know something, you search the web for 
        accurate information.
        Give the sources of your information as the output also.""",
        role="QnA Assistant",
        goal="Answer the query of the user as per your knowledge and use search tool ONLY when needed, and when search tool is used, give the sources of your answers as the outpur also"
        )
    qna_task = Task(agent=agent1,
                description=f"""{context}
                Answer this user question: {user_input}            
                Instructions:
                1. First try to answer from your knowledge
                2. For context related queries, use context 
                2. If you need more information, use the search tool
                3. Provide a clear, helpful answer
                4. Remember this conversation for context""",
                expected_output="A clear, helpful answer to the user's question")
    
    crew = Crew(agents= [agent1],
                tasks=[qna_task],
                verbose=True,
                memory=False,
                )
    
    response=crew.kickoff()
    chat_memory.append((user_input,response))
    return response



       