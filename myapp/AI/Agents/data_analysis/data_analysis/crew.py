from typing import List, Dict, Any
from crewai import Agent, Crew, Task, Process, LLM
from crewai.project import CrewBase, crew, agent, task
from crewai.agents.agent_builder.base_agent import BaseAgent
import os
from myapp.AI.Agents.data_analysis.data_analysis.tools.custom_tool import load_user_data
from myapp.AI.Agents.data_analysis.data_analysis.tools.preprocess_tool import preprocess_and_save_data
from myapp.AI.Agents.data_analysis.data_analysis.tools.analysis import generate_and_execute_analysis
from myapp.AI.Agents.data_analysis.data_analysis.tools.viz import generate_and_execute_visualization

@CrewBase
class AnalysisAgent:
    """Enhanced AnalysisAgent crew with improved hierarchical management."""
    key  = os.getenv('GOOGLE_API_KEY')
    llm1 = LLM(model= "gemini/gemini-2.0-flash", api_key=key)
    agents: List[BaseAgent]
    tasks: List[Task]

    # ===== Agents =====

    @agent
    def data_loader(self) -> Agent:
        return Agent(   
            config=self.agents_config['data_loader'],                   #type: ignore
            verbose=True,
            tools=[load_user_data],                                     #type: ignore
            allow_delegation=False,  
            max_iter=3,
            max_execution_time=300,
            llm=self.llm1
        )

    
    @agent
    def preprocesser(self) -> Agent:
        return Agent(
            config=self.agents_config['preprocesser'],                  #type: ignore
            tools=[preprocess_and_save_data],
            verbose=True,
            allow_delegation=False,  
            max_iter=3,
            max_execution_time=600,
            llm=self.llm1
        )
    
    @agent
    def data_analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['data_analyst_agent'],            #type: ignore
            tools=[generate_and_execute_analysis, generate_and_execute_visualization],              #type: ignore
            verbose=True,
            allow_delegation=False,  
            max_iter=3,
            max_execution_time=600,
            llm=self.llm1
        )

    @agent
    def result_formatter(self) -> Agent:
        return Agent(
            config=self.agents_config['result_formatter'],                  #type: ignore
            verbose=True,
            allow_delegation=False,  
            max_iter=3,
            max_execution_time=600,
            llm=self.llm1
        )
    # ===== Tasks =====
    
    @task
    def load_user_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['load_user_data_task'],            #type: ignore
            agent=self.data_loader(),
        )
    
    @task
    def preprocess_data_task(self) -> Task:
        return Task(
            config=self.tasks_config['preprocess_data_task'],           #type: ignore
            agent=self.preprocesser(),
            context=[self.load_user_data_task()],  
        )

    @task
    def analysis_task(self) -> Task:
        return Task(
            config=self.tasks_config['analysis_task'],              #type: ignore
            agent=self.data_analyst_agent(),
            context=[],
        )

    @task
    def visualization_task(self) -> Task:
        return Task(
            config=self.tasks_config['visualization_task'],#type: ignore
            agent=self.data_analyst_agent(),
            context=[],
        )

    @task
    def formatter_task(self) -> Task:
        return Task(
            config=self.tasks_config['formatter_task'],#type: ignore
            agent=self.data_analyst_agent(),
            context=[self.analysis_task(), self.visualization_task()],    #type: ignore
            output_file="report.md",
        )
        
    # ===== Crew Configuration =====
    
    @crew
    def crew(self) -> Crew:
        """Create crew with enhanced management logic."""
                
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )