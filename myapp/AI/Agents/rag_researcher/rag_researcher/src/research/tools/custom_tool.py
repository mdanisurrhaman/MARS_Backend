import os
from urllib.parse import urlparse
from pathlib import Path
from crewai_tools import RagTool
# from agents.rag_researcher.src.research.tools.rag_tool_config import tool_config
from myapp.AI.Agents.rag_researcher.rag_researcher.src.research.tools.rag_tool_config import tool_config


rag_tool = RagTool(config=tool_config)
rag_agent=[]

def add_to_rag(source: str):
    source = source.strip()

    def is_url(s):
        try:
            result = urlparse(s)
            return all([result.scheme, result.netloc])
        except:
            return False

    path = Path(source)

    if is_url(source):
        rag_agent=rag_tool.add(data_type="web_page", source=source)

    elif path.is_file():
        ext = path.suffix.lower()
        if ext == '.pdf':
            rag_agent=rag_tool.add(data_type="pdf_file", source=str(path))
            print(rag_agent)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Only .pdf is allowed.")

    else:
        raise ValueError(f"Invalid source: {source}. Only web URLs or PDF files are supported.")
    
    return rag_agent