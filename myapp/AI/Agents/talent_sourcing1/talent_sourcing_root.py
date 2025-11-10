import os
from dotenv import load_dotenv
from myapp.AI.Agents.talent_sourcing1.crew import tech_recruitment_crew 
from crewai.tools import tool
from crewai import LLM

# Load environment variables from the .env file
load_dotenv()

# --- Configuration Check ---
if not os.getenv("GITHUB_TOKEN"):
    raise ValueError("GITHUB_TOKEN environment variable not set. Please create a .env file with your token.")
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY environment variable not set. Please create a .env file with your key.")


def num_of_candidates(query:str)->int:
        key  = os.getenv('GOOGLE_API_KEY')
        llm = LLM(model= "gemini/gemini-2.0-flash", api_key=key)    
        result = int(llm.call(f"""Fetch the number of candidates from {query}, and return a SINGLE NUMBER as a response.
                          If the number of candidates is not specified by the  user, give 10 as the response."""))
        return result

@tool
def run_talent_sourcing(query:str):
    """Run the talent sourcing crew. Takes in job description as query and gives candidates from Github."""
    numberofcandidates = num_of_candidates(query)
    result = tech_recruitment_crew.kickoff(inputs={'job_description': query, 'num_candidates': numberofcandidates})
    return result
 


