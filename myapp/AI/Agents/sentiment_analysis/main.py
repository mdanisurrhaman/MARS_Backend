#!/usr/bin/env python
from myapp.AI.Agents.sentiment_analysis.crew import Sentiment_analysis_crew

# This main file is intended to be a way for your to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information


def run():
    """
    Run the crew.
    """
    inputs = {
        "reviews_file": "dummy_Data/Reviews.json",  # Example input, adjust as needed
        "file_type": "json",
    }

    result = Sentiment_analysis_crew().crew().kickoff(inputs=inputs)

    print(result)



if __name__ == "__main__":
    run()

