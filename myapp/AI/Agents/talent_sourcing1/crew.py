import os
from crewai import Agent, Task, Crew, Process, LLM
from myapp.AI.Agents.talent_sourcing1.tools.githubsearch import GitHubCandidateSearchTool
from myapp.AI.Agents.talent_sourcing1.tools.jdparser import jdParser
from dotenv import load_dotenv

load_dotenv()

# Instantiate the custom tools
jd_parser_tool = jdParser()
github_search_tool = GitHubCandidateSearchTool()


llm = LLM(model="gemini/gemini-2.0-flash", api_key=os.getenv("GEMINI_API_KEY"))

# Define the JD Parser Agent
jd_parser_agent = Agent(
    role="Job Description Analyst",
    goal="""
        Precisely and creatively extract the core job role and location from any job description,
        regardless of its format or length. Your ultimate goal is to convert this information
        into a single, effective GitHub search query.
    """,
    backstory=(
        "You are an expert AI with a keen eye for detail, specializing in transforming "
        "informal and formal job descriptions into structured search queries."
        "You can infer job roles from descriptive text and are an expert at identifying "
        "location data, even when it's not explicitly stated. Your purpose is to "
        "generate the most relevant GitHub search string possible for a candidate searcher."
    ),
    tools=[jd_parser_tool],
    verbose=False,
    allow_delegation=False,
    llm=llm
)

# Define the GitHub Candidate Searcher Agent
recruiter_agent = Agent(
    role="GitHub Candidate Searcher",
    goal="""
    Use a given GitHub search query to find potential candidates and save their 
    details to a file,You must use the GitHub Candidate Searcher tool for this task.                                        
    """,
    backstory=(
        "You are an experienced technical recruiter specializing in sourcing talent from GitHub. "
        "You are a master at using search queries to efficiently find and extract "
        "relevant candidate profiles."
    ),
    tools=[github_search_tool],
    verbose=False,
    allow_delegation=False,
    llm=llm)


# Define the Tasks
jd_parsing_task = Task(
    description=(
        "Analyze the following job description: '{job_description}'. "
        "Follow these strict rules to generate a GitHub search query: \n"
        "1. *Identify the Job Role:* Find the primary job title or role. If it's not a clear title like 'Software Engineer,' try to infer it from the context (e.g., 'coder' or 'developer' can become 'Software Developer').\n"
        "2. *Identify the Location:* Find the specific geographic location (city, state, country). If no location is mentioned, use the value 'unknown'.\n"
        "3. *Identify the Primary Programming Language:* Scan the job description for keywords related to programming languages or technology stacks, such as 'Python', 'Java', 'JavaScript', 'MERN', 'Django', 'Spring Boot', or 'React'. If a single primary language is found, use it.\n"
        "4. *Handle Ambiguity or Missing Data:* If no specific programming language can be identified from the description, you MUST NOT include a language filter in your query. If the job description contains NEITHER a clear job role NOR a location, your final output MUST be the exact message: 'please provide job role and location'.\n"
        "5. *Format the Output:* Your final answer MUST be a single line formatted as a GitHub search query. Do not include any extra text, explanations, or quotes. The format should be: "
        "'<job_role> in:bio location:<location_value> language:<language_value>'\n"
        "   - *Example with language:* For a 'Python Developer' in 'New Delhi', the output should be: 'python developer in:bio location:New Delhi language:python'\n"
        "   - *Example without language:* For a 'Full Stack Developer' in 'Berlin' with no language specified, the output should be: 'full stack developer in:bio location:Berlin'\n"
        "   - *Example with insufficient data:* 'please provide job role and location'\n"
        "You must use ONLY the information from the provided job description and adhere to this strict format."
    ),
    expected_output=("A single GitHub search query as a plain text block, for example:"
                     "'python developer in:bio location:india language:python'"
                     "OR 'full stack developer in:bio location:berlin'"
                     "OR the exact phrase 'please provide job role and location' if the input is insufficient."),
    agent=jd_parser_agent
)


recruitment_task = Task(
    description=(
        "Use the search query from the previous task to find up to *{num_candidates}* "
        "candidates on GitHub. The output of this task must be a JSON formatted string "
        "containing the profile details of the found candidates."
    ),
    expected_output=(
        "A JSON formatted string containing the found candidate profiles, "
        "or an error message if the search was unsuccessful. The output should not "
        "contain any additional text, just the raw JSON."
    ),
    agent=recruiter_agent,
    context=[jd_parsing_task]
)



# Instantiate the Crew
tech_recruitment_crew = Crew(
    agents=[jd_parser_agent, recruiter_agent],
    tasks=[jd_parsing_task, recruitment_task],
    process=Process.sequential,
    verbose=False
)