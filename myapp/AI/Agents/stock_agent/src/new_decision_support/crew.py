from myapp.AI.Agents.stock_agent.src.new_decision_support.tools.ticker_lookup_tool import ticker_lookup
from myapp.AI.Agents.stock_agent.src.new_decision_support.tools.stock_performance_tool import (
    company_research_tool,
    stock_performance_tool,
    basic_company_info_tool
)
from myapp.AI.Agents.stock_agent.src.new_decision_support.tools.company_researcher_tool import create_news_tool
from myapp.AI.Agents.stock_agent.src.new_decision_support.tools.plotly_stock_chart_tool import stock_line_plot
from crewai import LLM
from dotenv import load_dotenv
load_dotenv()
import os

# Alpha Vantage API Key - Get free key from: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Create the news tool instance
alpha_vantage_news_tool = create_news_tool(ALPHA_VANTAGE_API_KEY) # type: ignore[index]


from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class NewDecisionSupport():
    """NewDecisionSupport crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    key  = os.getenv('GOOGLE_API_KEY')
    llm1 = LLM(model= "gemini/gemini-2.0-flash", api_key=key)
    @agent
    def Company_extractor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['Company_extractor_agent'], # type: ignore[index]
            verbose=False,
            llm=self.llm1
        )

    @agent
    def Ticker_lookup_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['Ticker_lookup_agent'], # type: ignore[index]
            tools=[ticker_lookup],  
            verbose=False,
            llm=self.llm1
        )

    @agent
    def Stock_price_analyzer_agent(self) -> Agent:
        """Agent responsible for checking stock prices and performance"""
        return Agent(
            config=self.agents_config['Stock_price_analyzer_agent'], # type: ignore[index]
            tools=[
                company_research_tool,
                stock_performance_tool,
                basic_company_info_tool
            ],
            verbose=False,
            llm=self.llm1
        )

    @agent
    def Company_researcher_agent(self) -> Agent:
        """Agent responsible for conducting detailed company research"""
        return Agent(
            config=self.agents_config['Company_researcher_agent'], # type: ignore[index]
            tools=[
                alpha_vantage_news_tool
            ],
            verbose=False,
            llm=self.llm1
       )
    
    @agent
    def Chart_visualizer_agent(self) -> Agent:
        """Agent responsible for creating stock price visualizations"""
        return Agent(
            config=self.agents_config['Chart_visualizer_agent'],# type: ignore[index]
            tools=[stock_line_plot],
            verbose=False,                                           # type: ignore[index]
            llm=self.llm1
        )

    @agent
    def decision_support_agent(self) -> Agent:
        """Agent responsible for providing decision support based on analysis"""
        return Agent(
            config=self.agents_config['decision_support_agent'], # type: ignore[index]
            verbose=False,
            llm=self.llm1
        )


    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def company_extractor_task(self) -> Task:
        return Task(
            config=self.tasks_config['company_extractor_task'], # type: ignore[index]
        )

    @task
    def ticker_lookup_task(self) -> Task:
        return Task(
            config=self.tasks_config['ticker_lookup_task'], # type: ignore[index]
            # output_file='ticker_lookup_output.json'
        )

    @task
    def stock_price_analyzer_task(self) -> Task:
        """Task to analyze stock performance and current prices"""
        return Task(
            config=self.tasks_config['stock_price_analyzer_task'], # type: ignore[index]
        )

    @task
    def company_researcher_task(self) -> Task:
        """Task to conduct detailed company research"""
        return Task(
            config=self.tasks_config['company_researcher_task'], # type: ignore[index]
        )

    @task
    def chart_visualization_task(self) -> Task:
        """Task for creating comprehensive stock visualizations"""
        return Task(
            config=self.tasks_config['chart_visualization_task'], # type: ignore[index]
        )
    
    @task
    def decision_support_task(self) -> Task:
        """Task to provide decision support based on analysis"""
        return Task(
            config=self.tasks_config['decision_support_task'], # type: ignore[index]
            output_file='decision_support_report.md'
        )


    @crew
    def crew(self) -> Crew:
        """Creates the NewDecisionSupport crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=False,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )


