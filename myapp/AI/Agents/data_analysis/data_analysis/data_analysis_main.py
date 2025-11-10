import warnings
from myapp.AI.Agents.data_analysis.data_analysis.crew import AnalysisAgent
from crewai.tools import tool

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

@tool
def run_data_analysis(query:str ,file_path : str):   
    """This tool analyzes the given dataset and returns demanded insights."""     
    inputs = {
        "query": query,
        "file_path": file_path,
        # "timestamp": timestamp,
    }
    try:
        response = AnalysisAgent().crew().kickoff(inputs=inputs)
        return response.raw  
    except Exception as e:
        raise Exception(f"An error occurred while running the data analysis crew: {e}")



