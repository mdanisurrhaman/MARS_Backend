from crewai import LLM, Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
# from agents.rag_researcher.src.research.tools.custom_tool import rag_tool
from myapp.AI.Agents.rag_researcher.rag_researcher.src.research.tools.custom_tool import rag_tool

import os



@CrewBase
class Research_agent:
    """Research_agent crew"""
    
    key  = os.getenv('GOOGLE_API_KEY')
    llm = LLM(model= "gemini/gemini-2.0-flash", api_key=key)
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def research_coordinator(self) -> Agent:
        return Agent(config=self.agents_config["research_coordinator"], verbose=False, llm=self.llm)  # type: ignore

    @task
    def synthesize_task(self) -> Task:
        return Task(
            config=self.tasks_config["synthesize_task"],  # type: ignore
            agent=self.research_coordinator(),
            )

    @agent
    def knowledge_expert(self) -> Agent:
        """Agent that uses RagTool and dynamic source loading"""
        return Agent(
            config=self.agents_config["knowledge_expert"],  # type: ignore
            tools=[rag_tool],
            verbose=False,
            llm=self.llm
        )

    @task
    def knowledge_task(self) -> Task:
        return Task(
            config=self.tasks_config["knowledge_task"],  # type: ignore
            agent=self.knowledge_expert(),
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Research crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )
