import sys
from .crew import AutomationAgent
from datetime import datetime
from crewai.tools import tool
import os
def auto_run(query=None, file_path=None, csv_file=None):
    """
    Automation agent automatically searches for info and sends email.
    Run the crew with all required inputs.
    """
    # Ensure all expected input keys exist, even if empty
    inputs = {
        'query': query or "",
        'attach_file_path': file_path or "",  # Crew expects this key
        'csv_file': csv_file or "",           # Crew expects this exact key
        'date': datetime.now().strftime('%Y-%m-%d')
    }

    os.environ["CREW_QUERY"] = inputs["query"]
    # Kickoff the crew
    result = AutomationAgent().crew().kickoff(inputs=inputs)
    return result
