import sys
from myapp.AI.Agents.automation_agent2.src.automation.crew import AutomationAgent
from datetime import datetime
from crewai.tools import tool
import os


@tool
def automation_run(query:str, attachment_file_path:str, csv_file:str):
    """
    Run the Automation agent crew. Sends email to provided mails. The mails of the reciepients are given in query or in the csv_file """
    inputs = {
        'query': query,
        'attach_file_path':  attachment_file_path if attachment_file_path else None,  # Optional file path for attachment
        'csv_file':csv_file if csv_file else None,
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    os.environ["CREW_QUERY"] = inputs["query"]
    result = AutomationAgent().crew().kickoff(inputs=inputs)
    return result