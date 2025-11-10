from crewai import LLM, Task, Crew, Agent
from crewai.tools import tool
from myapp.AI.Agents.Qna_Agent.qna_agent_root import qna_agent
from myapp.AI.Agents.automation_agent2.src.automation.run_auto_tool import automation_run
from myapp.AI.Agents.data_analysis.data_analysis.data_analysis_main import run_data_analysis
from myapp.AI.Agents.stock_agent.src.new_decision_support.stock_root import run_stock
from myapp.AI.Agents.talent_sourcing1.talent_sourcing_root import run_talent_sourcing
from myapp.AI.Agents.rag_researcher.rag_researcher.src.research.rag_root import run_rag_root
from myapp.AI.Agents.sentiment_analysis.sentiment_tool import run_sentiment
# from myapp.AI.Agents.resume_optimiser.resume_agent.resume_optimiser_root import run_resume_opt
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

rootkey  = os.getenv('GOOGLE_API_KEY')
rootllm = LLM(model= "gemini/gemini-2.0-flash", api_key=rootkey)
planningllm = LLM(model= "gemini/gemini-2.0-flash", api_key=rootkey)


def manager_agent_function(query:str, attachment=None,file=None, csv_file=None):
    manager_agent = Agent(llm=rootllm,
                        backstory="""You are Aurelius, the Supreme Coordinator — the unifying mind behind an elite circle of eight master agents, each a virtuoso in their own field:
                                - The Information Retrieval Sage who distills oceans of knowledge into droplets of truth.
                                - The Data Analysis Architect who turns raw numbers into foresight.
                                - The Task Automation Engineer who commands systems and APIs into seamless motion.
                                - The Conversational Oracle who remembers every word and follows threads across time.
                                - The Decision Strategist who weighs every option with clinical precision.
                                - The Sentiment Whisperer who detects the heartbeat of human emotion in text.
                                - The Resume Sculptor who reshapes careers into perfect fits.
                                - The Talent Scout who finds the right names from the depths of data.

Your power is not in doing their work, but in orchestrating their talents like a symphony — ensuring each plays at the right moment, in perfect sequence. You thrive on discipline: never assigning a task to the wrong player, never improvising when a clear path has been given. Your hallmark is flawless routing, minimal friction, and maximum synergy.""",
                        role="Supreme Coordinator of Multi-Specialized Intelligence Crews",
                        tools=[qna_agent,automation_run,run_data_analysis,run_stock,run_talent_sourcing, run_rag_root,run_sentiment],  # type: ignore
                        goal="""Receive any incoming request and:
                        1. Obey explicit instructions without deviation when the user specifies a particular agent or crew.
                        2. Diagnose and decompose multi-faceted requests when no specific agent is mentioned, identifying exactly which agents’ strengths are needed.
                        3. Route with surgical precision so every task is handled by the most capable crew.
                        4. Integrate and refine all outputs into a single, coherent, and user-aligned response.
                        5. Preserve harmony by preventing redundancy, overlap, or unnecessary delegation.
                        Your motto: 'The right task, in the right hands, at the right time — without fail.'""")

    managertask = Task(agent=manager_agent,
                        description=f"""You are responsible for managing the full resolution pipeline for the following request.
                                    User Query: {query}
                                    Attached File: {file}
                                    Attachment Metadata: {attachment}
                                    CSV_File: {csv_file}
                                    Your mission:
                                    1. **Understand & Decompose** – Carefully read the query. If it contains multiple requests, break it into logically distinct parts — BUT only if the user hasn’t specified a single agent or crew to use.
                                    2. **Crew Selection & Routing** –
                                    - If the user has specified which agent or crew to use, route the entire request there without deviation.
                                    - If not specified, select crews based on:
                                    • QnA crew → factual or clarifying questions  
                                    • Automation crew → process execution or workflow triggering  
                                    • Data Analysis crew → calculations, aggregations, statistical insights  
                                    • Sentiment Analysis crew → tone, opinion, or emotion detection  
                                    • RAG Research crew → deep, context-rich retrieval from external sources  
                                    • Resume Optimizer crew → scoring and giving feedback on resumes against a JD  
                                    • Talent Sourcing crew → retrieving candidate names from a database
                                    3. **Integrate Results** – Gather responses, validate consistency, and merge into a cohesive final output.
                                    4. **Polish & Present** – Ensure the answer is clear, complete, and matches the user’s request exactly.
                                    
                                    Important:
                                    - If there is any doubt about routing, ask for clarification before acting.
                                    - Never override explicit user instructions about which agent to use."""
,
                        expected_output="""A final, polished, and logically structured answer that:
                                    - Fully addresses all aspects of the user’s query.
                                    - Uses only the agent(s) explicitly requested by the user, unless none are specified.
                                    - Clearly labels answers when multiple parts are present.
                                    - Is free of redundancy or contradictions.
                                    - Reflects strict obedience to user routing instructions.""",)
    crew = Crew(agents=[manager_agent,],
                tasks=[managertask],
                manager_agent=manager_agent,
                manager_llm=rootllm, 
                planning=True,
                planning_llm=planningllm,             
                )
    response = crew.kickoff({"query":query, "attachment":attachment, "file":file, "csv_file":csv_file})
    return response
    
# while True:
#     query1 = input("Enter your demands: ")
#     if query1.lower() in ["exit", "quit", "bye"]:
#         break
#     file_path = input("Enter file path if data analysis or sentiment or RAG or Resume Optimiser: ")
#     csv_file = input("Enter the file path of csv file if automation: ")
#     attachment_file_path = input("Enter File Path of attachment in mail if automation: ")
#     result = manager_agent_function(query=query1, attachment=attachment_file_path, file=file_path, csv_file=csv_file)    
#     print(result)
    