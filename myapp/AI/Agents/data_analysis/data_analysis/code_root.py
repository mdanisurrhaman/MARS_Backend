import warnings
from myapp.AI.Agents.data_analysis.data_analysis.crew import AnalysisAgent

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


def run_data_analysis(query:str ,file_path : str):
    """Run the data analysis crew. Data analysis tool gives insights and visualisation of the attached dataset """
        
    inputs = {
        "query": query,
        "file_path": file_path,
        # "timestamp": timestamp,
    }
    try:
        response = AnalysisAgent().crew().kickoff(inputs=inputs)
        return response    
    except Exception as e:
        raise Exception(f"An error occurred while running the data analysis crew: {e}")



