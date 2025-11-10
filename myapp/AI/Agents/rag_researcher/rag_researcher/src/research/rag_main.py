import warnings
# from agents.rag_researcher.src.research.crew import Research_agent
# from agents.rag_researcher.src.research.crew import Research_agent
# from agents.rag_researcher.src.research.tools.custom_tool import add_to_rag
from myapp.AI.Agents.rag_researcher.rag_researcher.src.research.crew import Research_agent
from myapp.AI.Agents.rag_researcher.rag_researcher.src.research.tools.custom_tool import add_to_rag


warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# def rag_run(query, file_path):
#     inputs = {
#         "query":query, 
#         "source": file_path
#     }

#     add_to_rag(inputs["source"])

#     Research_agent().crew().kickoff(inputs=inputs)
def rag_run(query: str, file_path: str) -> str:
    inputs = {
        "query": query,
        "source": file_path
    }

    add_to_rag(inputs["source"])

    result = Research_agent().crew().kickoff(inputs=inputs)
    print(result.raw)
    return result.raw

