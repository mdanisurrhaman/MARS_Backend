from crewai import Agent, Crew, Process, Task,LLM
from crewai.project import CrewBase, agent, crew, task
# from crewai.tools import SerperDevTool
from pydantic import BaseModel, Field
from typing import List, Dict
from myapp.AI.Agents.automation_agent2.src.automation.tools.email import send_email_smtp  
import re
import os


class ResearchPoint(BaseModel):
    topic: str = Field(description="The main topic in query or area being discussed")
    findings: str = Field(description="The key findings or insights about this topic topic in query")
    relevance: str = Field(description="Why this finding is relevant or important")
    sources: List[Dict[str, str]] = Field(
        description="Sources with title and URL for each finding",
        default_factory=list
    )

class ResearchOutput(BaseModel):
    research_points: List[ResearchPoint] = Field(description="List of research findings")
    summary: str = Field(description="Brief summary of overall findings")

class ExecutiveReportSection(BaseModel):
    section_title: str = Field(description="Section title")
    section_content: str = Field(description="Main content of the section")
    key_insights: List[str] = Field(description="Key insights from this section")
    recommendations: List[str] = Field(
        default_factory=list,
        description="Optional recommendations based on findings"
    )
    sources: List[Dict[str, str]] = Field(
        description="Sources with title and URL for this section",
        default_factory=list
    )

class ExecutiveReport(BaseModel):
    report_title: str = Field(description="Title of the report")
    generation_date: str = Field(description="Report generation date")
    executive_summary: str = Field(description="A concise executive summary")
    key_findings: List[Dict[str, str]] = Field(
        description="List of key findings with their sources",
        default_factory=list
    )
    report_sections: List[ExecutiveReportSection] = Field(
        description="Detailed report sections"
    )
    next_steps: List[str] = Field(description="Recommended next steps")
    sources: List[Dict[str, str]] = Field(
        description="All sources used in the report",
        default_factory=list
    )
	
@CrewBase
class AutomationAgent():
    """AutomationAgent crew"""
    
    key  = os.getenv('GOOGLE_API_KEY')
    llm1 = LLM(model= "gemini/gemini-1.5-flash", api_key=key)
    
        
    @agent
    def researcher(self) -> Agent:
        """        Researcher agent to uncover cutting-edge developments on a given topic.
        """
        return Agent(
            config=self.agents_config['researcher'],            #type: ignore
            verbose=True,                           #type: ignore
            # tools=[SerperDevTool()],
            llm=self.llm1
        )

    @agent
    def reporting_analyst(self) -> Agent:
        """Reporting Analyst agent to create detailed reports based on research findings.
          Reporting Analyst agent to create detailed reports based on research findings."""
        return Agent(
            config=self.agents_config['reporting_analyst'], #type: ignore
            verbose=True,
            llm=self.llm1
        )
    @agent
    def formatter(self) -> Agent:
        """ Formatter agent to format the report and prepare it for email if email adress is provided in query."""
        return Agent(
            config=self.agents_config['formatter'],#type: ignore
            verbose=True,
            llm=self.llm1
       )
    
    
    @agent
    def email_writer(self) -> Agent:
        """Agent to compose professional or personal email bodies."""
        return Agent(
        config=self.agents_config['email_writer'],          #type: ignore
        verbose=True  ,
            llm=self.llm1                                  
        )

    @task
    def write_email_body(self) -> Task:
         """Task to generate a polished email body from user query."""
         return Task(
            config=self.tasks_config['write_email_body'],   #type: ignore
            
    )

    @agent
    def email_assistant(self) -> Agent:
        """Email Assistant agent to send emails with the report and attachments."""
        return Agent(
            config=self.agents_config['email_assistant'],   #type: ignore
            tools=[send_email_smtp],
            verbose=True,
            llm=self.llm1
        )
    
    
    @task
    def research_task(self) -> Task:
        """Task to perform research on a given topic."""
        return Task(
            config=self.tasks_config['research_task'],          #type: ignore
            output_json=ResearchOutput
        )

    @task
    def reporting_task_long(self) -> Task:
       return Task(
        config=self.tasks_config['reporting_task_long'],                #type: ignore
        output_pydantic=ExecutiveReport
    )

    @task
    def reporting_task_short(self) -> Task:
        return Task(
        config=self.tasks_config['reporting_task_short'],               #type: ignore
        output_pydantic=ExecutiveReport
    )

    @task
    def formatting_task(self) -> Task:
        """Task to format the report and prepare it for email."""
        return Task(    
            config=self.tasks_config['formatting_task'],            #type: ignore                
        )
    
    @task
    def send_email_task(self) -> Task:
        """Task to send an email with the report and attachments and writen meesage."""
        return Task(
            config=self.tasks_config['send_email_task']#type: ignore

        )
    
    @crew
    def crew(self) -> Crew:
        query = os.getenv("CREW_QUERY", "").lower()

        has_email = "csv" in query or re.search(r"[\w\.-]+@[\w\.-]+", query)
        wants_report = any(word in query for word in ["report", "research", "generate report", "create report"])
        has_custom_message = re.search(r"(?:message|send this message|write this message)\s+'([^']+)'", query)

        if has_email:
            if wants_report and has_custom_message:
                selected_tasks = [
                    self.research_task(),
                    self.reporting_task_short(),
                    self.formatting_task(),
                    self.write_email_body(),
                    self.send_email_task()
                ]
            elif wants_report:
                selected_tasks = [
                    self.research_task(),
                    self.reporting_task_short(),
                    self.formatting_task(),
                    self.send_email_task()
                ]
            elif has_custom_message:
                selected_tasks = [
                    self.write_email_body(),
                    self.send_email_task()
             ]
            else:
                selected_tasks = [
                 self.write_email_body(),
                 self.send_email_task()
                ]
        else:
            if wants_report:
             selected_tasks = [
                 self.research_task(),
                 self.reporting_task_long(),
                 self.formatting_task()
             ]
            else:
              selected_tasks = [
              self.write_email_body()
             ]

        return  Crew(
            agents=self.agents,           #type: ignore
            tasks=selected_tasks,
            process=Process.sequential,
            planning=True,
            planning_llm="gemini/gemini-2.0-flash" ,
            verbose=True
        )
    

    