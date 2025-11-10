#!/usr/bin/env python
from myapp.AI.Agents.sentiment_analysis.crew import Sentiment_analysis_crew
from crewai.tools import tool
import os

# This main file runs your sentiment analysis crew locally
# or via the Django backend API. It now supports file_path and csv_file.

@tool
def run_sentiment(file_path: str = None, csv_file: str = None):
    """
    Run sentiment analysis on a file or CSV.
    
    Args:
        file_path (str): Path to a regular file.
        csv_file (str): Path to a CSV file.
        
    Returns:
        dict: Sentiment analysis results.
    """
    # Determine which file to use
    target_file = file_path or csv_file
    if not target_file:
        return {"error": "No file provided"}

    # Determine file type from extension
    file_type = os.path.splitext(target_file)[1].lstrip('.').lower()

    # Inputs for the crew
    inputs = {
        "reviews_file": target_file,
        "file_type": file_type,
    }

    # Run the crew
    result = Sentiment_analysis_crew().crew().kickoff(inputs=inputs)
    return result
