from crewai.tools import BaseTool

class jdParser(BaseTool):
    """
    A tool that serves as a placeholder for the JD Parser Agent.
    The agent's LLM handles the actual parsing logic via the task description.
    """
    name: str = "Job Description Parser"
    description: str = "A tool to signal the agent to parse a job description."

    def _run(self, *args, **kwargs) -> str:
        """
        The LLM in the agent handles the parsing logic directly,
        making this tool's run method a placeholder.
        """
        # The agent's LLM uses the task's prompt to perform the parsing.
        # This tool itself does not need to perform any action.
        return "Parsing job description using the agent's LLM."
