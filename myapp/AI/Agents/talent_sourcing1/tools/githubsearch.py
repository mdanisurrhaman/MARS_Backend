import os
import requests
import time
import json
from typing import Optional, Any, List, Dict
from crewai.tools import BaseTool
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Set up the API headers for authentication
HEADERS = {}

class GitHubCandidateSearchTool(BaseTool):
    """
    A custom tool for searching for candidates on GitHub using a specific search query.
    """
    name: str = "GitHub Candidate Searcher"
    description: str = (
        "A tool to search for potential candidates on GitHub using a search query and a target number of profiles. "
        "The query must follow GitHub's search syntax, e.g., 'location:india language:java "
        "junior in:bio followers:>10'. The tool will fetch up to the specified number of profiles that have an email address."
    )
    
    def _run(self, search_query: str, num_candidates: int) -> str:
        """
        Executes the GitHub candidate search and returns the results as a JSON string.
        
        Args:
            search_query (str): The search query string for GitHub.
            num_candidates (int): The target number of candidates with emails to find.

        Returns:
            str: A JSON string containing the found candidate data or an error message.
        """
        print(f"Starting GitHub search for query: '{search_query}' to find {num_candidates} profiles with emails.")
        
        # Check for the GitHub token before making any requests
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            error_msg = "GITHUB_TOKEN environment variable not set. Please add it to your .env file."
            print(f"Error: {error_msg}")
            return json.dumps({"error": error_msg}, indent=4)
        
        HEADERS['Authorization'] = f'token {github_token}'
        HEADERS['Accept'] = 'application/vnd.github.v3+json'

        try:
            # Get the list of profiles directly from the helper function
            final_profiles = self._get_and_process_candidates(search_query, num_candidates)
            
            # Prepare the JSON output
            if not final_profiles:
                json_output = {"message": "No candidates were found with the generated search query and email addresses."}
            else:
                filtered_profiles = []
                for candidate in final_profiles:
                    filtered_profiles.append({
                        "name": candidate.get("name"),
                        "company": candidate.get("company"),
                        "blog": candidate.get("blog"),
                        "location": candidate.get("location"),
                        "email": candidate.get("email"),
                        "hireable": candidate.get("hireable"),
                        "bio": candidate.get("bio"),
                        "public_repos": candidate.get("public_repos")
                    })
                
                json_output = {
                    "profiles_with_email": filtered_profiles
                }

            # Return the JSON string
            print(f"Total candidates with email processed: {len(final_profiles)}")
            return json.dumps(json_output, indent=4)

        except Exception as e:
            error_msg = f"An unexpected error occurred during the GitHub search: {e}"
            print(error_msg)
            return json.dumps({"error": error_msg}, indent=4)

    def _normalize_linkedin_url(self, url: str) -> str:
        """
        Helper to format a LinkedIn URL correctly by cleaning up common issues.
        """
        if 'linkedin.com' in url:
            url = url.split('?')[0].rstrip('/')
            if url.startswith('https://linkedin.com/in/in/'):
                url = url.replace('https://linkedin.com/in/in/', 'https://www.linkedin.com/in/')
            elif url.startswith('https://www.linkedin.com/in/in/'):
                url = url.replace('https://www.linkedin.com/in/in/', 'https://www.linkedin.com/in/')
            if not url.startswith('https://www.linkedin.com/in/'):
                url = url.replace('https://linkedin.com/', 'https://www.linkedin.com/in/')
        return url
        
    def _get_full_candidate_details(self, username: str) -> Optional[dict]:
        """
        Fetches detailed information for a single GitHub user.
        """
        try:
            user_url = f"https://api.github.com/users/{username}"
            response = requests.get(user_url, headers=HEADERS)
            response.raise_for_status()
            user_data = response.json()

            if user_data.get('blog') and isinstance(user_data.get('blog'), str):
                user_data['blog'] = self._normalize_linkedin_url(user_data['blog'])

            return user_data

        except requests.exceptions.HTTPError as e:
            print(f"Error fetching details for {username}: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred for {username}: {e}")
            return None

    def _get_and_process_candidates(self, search_query: str, num_candidates: int) -> List[Dict[str, Any]]:
        """
        Performs a paged search and returns a list of candidate dictionaries.
        """
        base_url = "https://api.github.com/search/users"
        profiles_with_email = []
        page = 1
        per_page = 100

        # Continue searching as long as we haven't found enough candidates
        while len(profiles_with_email) < num_candidates:
            params = {
                'q': search_query,
                'per_page': per_page,
                'page': page
            }
            
            try:
                response = requests.get(base_url, headers=HEADERS, params=params)
                print(f"GitHub API Response Status (Page {page}): {response.status_code}")
                response.raise_for_status()

                remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                
                if remaining < 10:
                    wait_time = reset_time - time.time() + 5
                    print(f"Approaching rate limit. Waiting for {wait_time:.2f} seconds.")
                    time.sleep(wait_time)

                data = response.json()
                users = data.get('items', [])
                if not users:
                    print("No more candidates found or end of search results.")
                    break

                for user in users:
                    username = user.get('login')
                    if username:
                        full_details = self._get_full_candidate_details(username)
                        if full_details and full_details.get('email'):
                            profiles_with_email.append(full_details)
                            print(f"Found and processed candidate with email: {full_details.get('login')}")
                            # Stop if we've reached the desired number of candidates
                            if len(profiles_with_email) >= num_candidates:
                                break

                # Stop searching if we've reached the target
                if len(profiles_with_email) >= num_candidates:
                    break

                page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                if e.response:
                    print(f"API Response Text: {e.response.text}")
                break

        return profiles_with_email[:num_candidates]