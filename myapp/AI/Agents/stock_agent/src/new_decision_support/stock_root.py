#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
from myapp.AI.Agents.stock_agent.src.new_decision_support.crew import NewDecisionSupport
from crewai.tools import tool
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

@tool 
def run_stock(query:str):
    """
    Run the stock market analysis crew.
    """    
   
    result= NewDecisionSupport().crew().kickoff(inputs={
                                                'topic': query, 
                                                'current_year': str(datetime.now().year),
                                                'current_date': datetime.now().strftime('%Y-%m-%d')
        })
    return result
   