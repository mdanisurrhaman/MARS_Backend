import os
import fitz
import docx
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

# ---------- Text extraction logic ----------
def extract_text(input_source: str) -> str:
    """
    Extracts text from .pdf, .docx, .txt files or treats the input as a raw string.
    """
    def read_pdf(file_path):
        try:
            with fitz.open(file_path) as doc:
                return "".join(page.get_text() for page in doc)
        except Exception as e:
            print(f"Error reading PDF file: {e}")
            return ""

    def read_docx(file_path):
        try:
            doc = docx.Document(file_path)
            return "\n".join(para.text for para in doc.paragraphs)
        except Exception as e:
            print(f"Error reading DOCX file: {e}")
            return ""

    def read_txt(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading TXT file: {e}")
            return ""

    if os.path.isfile(input_source):
        _, ext = os.path.splitext(input_source)
        ext = ext.lower()
        reader_map = {'.pdf': read_pdf, '.docx': read_docx, '.txt': read_txt}
        if ext in reader_map:
            return reader_map[ext](input_source)
        else:
            raise ValueError(f"Unsupported file format: '{ext}'. Use .pdf, .docx, or .txt.")
    elif isinstance(input_source, str):
        return input_source
    else:
        raise FileNotFoundError(f"Invalid input: {input_source}")

# ---------- Crew/Agent/Task Definitions ----------
load_dotenv()
llm = LLM(model='gemini/gemini-2.0-flash')

@CrewBase
class ResumeOpt():
    """ResumeOpt crew for resume-job description matching and feedback"""
    agents_config = 'agents.yaml'
    tasks_config = 'tasks.yaml'

    @agent
    def scoring_agent(self):
        from crewai import Agent
        return Agent(
            config=self.agents_config['scoring_agent'],
            verbose=False,
            llm=llm
        )

    @agent
    def feedback_agent(self):
        from crewai import Agent
        return Agent(
            config=self.agents_config['feedback_agent'],
            verbose=False,
            llm=llm
        )

    @task
    def scoring_task(self):
        from crewai import Task
        return Task(
            config=self.tasks_config['scoring_task'],
            agent=self.scoring_agent()
        )
    
    @task
    def feedback_task(self):
        from crewai import Task
        return Task(
            config=self.tasks_config['feedback_task'],
            agent=self.feedback_agent()
        )

    @crew
    def crew(self):
        from crewai import Crew, Process
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=False,
        )

# ---------- End-to-end Runner Function ----------
def run_resume_opt(resume_path, jd_path):
    resume_text = extract_text(resume_path)[:3000]
    job_description_text = extract_text(jd_path)[:3000]
    inputs = {
        'resume': resume_text,
        'job_description': job_description_text
    }
    crew_result = ResumeOpt().crew().kickoff(inputs=inputs)
    return crew_result.raw
