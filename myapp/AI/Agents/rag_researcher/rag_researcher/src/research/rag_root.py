import warnings
# from agents.rag_researcher.src.research.crew import Research_agent
# from agents.rag_researcher.src.research.crew import Research_agent
# from agents.rag_researcher.src.research.tools.custom_tool import add_to_rag
from myapp.AI.Agents.rag_researcher.rag_researcher.src.research.crew import Research_agent
from myapp.AI.Agents.rag_researcher.rag_researcher.src.research.tools.custom_tool import add_to_rag
from crewai.tools import tool
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

@tool
def run_rag_root(query:str, file_path:str):
    """Run the Rag researcher crew."""
    inputs = {
        "query":query,
        "source": file_path
    }

    add_to_rag(inputs["source"])
    result = Research_agent().crew().kickoff(inputs=inputs)
    return result.raw

