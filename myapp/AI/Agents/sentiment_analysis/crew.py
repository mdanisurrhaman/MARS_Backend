from crewai import Agent, Crew, Process, Task,LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from myapp.AI.Agents.sentiment_analysis.tools.custom_tools import AnalyzeReviewsTool
from crewai_tools import FileReadTool
import os

tool_config = dict(
    llm=dict(
        provider="google",
        config=dict(
            model="gemini-2.0-flash-lite",
        ),
    ),
    embedder=dict(
        provider="google",
        config=dict(
            model="models/embedding-001",
            task_type="retrieval_document",
        ),
    ),
)


@CrewBase
class Sentiment_analysis_crew:
    """Sentiment Analysis crew"""
    key  = os.getenv('GOOGLE_API_KEY')
    llm = LLM(model= "gemini/gemini-2.0-flash", api_key=key)
    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def fileloader(self) -> Agent:
        return Agent(
            config=self.agents_config["fileloader"],  # type: ignore
            tools=[
                FileReadTool(config=tool_config, result_as_answer=True),
            ],
            verbose=True,
            llm=self.llm
        )

    @task
    def load_reviews(self) -> Task:
        return Task(
            config=self.tasks_config["load_reviews"],  # type: ignore
            tools=[
                FileReadTool(config=tool_config, result_as_answer=True),
            ]
        )

    @agent
    def sentiment_emotion_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config["sentiment_emotion_analyzer"],  # type: ignore
            tools=[AnalyzeReviewsTool(result_as_answer=True)],
            llm=self.llm
        )


    @task
    def analyze_sentiment(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_sentiment_and_emotion"],  # type: ignore
            tools=[AnalyzeReviewsTool()],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Sentiment_Analysis crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
