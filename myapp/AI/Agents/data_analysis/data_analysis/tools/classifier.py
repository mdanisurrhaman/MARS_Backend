import re
import json
from crewai import LLM
from dotenv import load_dotenv

load_dotenv()

# Initialize CrewAI LLM with error handling
try:
    llm = LLM(
        model="gemini/gemini-2.0-flash-001",  
        temperature=0
    )
except Exception as e:
    print(f" LLM initialization failed: {e}")
    llm = None

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    'import os', 'import sys', 'import subprocess', 'import socket',
    'eval(', 'exec(', '__import__', 'open(', 'file(', 'input(',
    'raw_input(', 'compile(', 'globals(', 'locals(', 'vars(',
    'dir(', 'hasattr(', 'getattr(', 'setattr(', 'delattr('
]


def get_data_path_from_query(user_query: str) -> str:
    """
    Given a user query, determine whether to use raw or preprocessed data.
    Returns the appropriate dataset path: 'data/raw_data.csv' or 'data/decoded.csv'.
    """

    if llm is None:
        print("LLM not initialized, defaulting to decoded data.")
        return 'data/decoded.csv'
    
    prompt = f"""
Classify this data analysis query on two dimensions:

1. DATA_TYPE needed:
   - "raw": Use original data for queries about missing values, original text data, data quality issues, original categories, data cleaning needs
   - "decoded": Use cleaned/decoded data for statistical analysis, modeling, correlations, aggregations, mathematical operations

Query: "{user_query}"

IMPORTANT: 
- If query mentions "missing values", "null", "NaN", "original categories", "text data", "data quality" → use "raw"
- If query asks for statistics, correlations, modeling, mathematical operations → use "decoded"
- If query asks for plots/visualizations of encoded data or analysis → use "decoded"
- If query asks to see original text values or categories in visualization → use "raw"

Return ONLY this JSON format:
{{"data_type": "raw|decoded"}}
"""

    try:
        result = llm.call(prompt)
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            classification = json.loads(json_match.group())
            data_type = classification.get("data_type", "decoded")
        else:
            print("No JSON found in LLM response. Defaulting to decoded.")
            data_type = "decoded"
    except Exception as e:
        print(f"Error during LLM call: {e}. Defaulting to decoded.")
        data_type = "decoded"

    # Map to file path
    if data_type == "raw":
        return "data/raw_data.csv"
    else:
        return "data/decoded.csv"

