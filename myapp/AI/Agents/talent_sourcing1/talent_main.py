import os
from dotenv import load_dotenv
from .crew import tech_recruitment_crew 

# Load environment variables from the .env file
load_dotenv()

def run_recruitment_crew(query: dict):
    """
    Guides the user through the recruitment process, collecting a job
    description and the number of candidates, then kicks off the crew.
    """
    # --- Configuration Check ---
    if not os.getenv("GITHUB_TOKEN"):
        raise ValueError("GITHUB_TOKEN environment variable not set. Please create a .env file with your token.")
    if not os.getenv("GEMINI_API_KEY"):
        raise ValueError("GEMINI_API_KEY environment variable not set. Please create a .env file with your key.")

    # ✅ Get job description from dict
    jd = query.get("description", "")

    # Check for empty input
    if not jd.strip():
        return {"error": "Job description cannot be empty."}
    
    # ✅ Get number of candidates from dict
    try:
        num_candidates = int(query.get("total_candidates", 10))
    except (ValueError, TypeError):
        num_candidates = 10

    # Kick off the crew with the user's input
    result = tech_recruitment_crew.kickoff(
        inputs={
            "job_description": jd,
            "num_candidates": num_candidates
        }
    )

    return {
        "job_description": jd,
        "num_candidates": num_candidates,
        "result": result
    }
