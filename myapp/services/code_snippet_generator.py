# services/code_snippet_generator.py

def generate_code_snippet(agent_name, api_key, url, method="GET", body=None, language="python"):
    """
    Generate integration code snippet for different languages.
    Defaults to Python.
    """
    if language.lower() == "python":
        return f"""import requests

url = "{url}"
headers = {{
    "Authorization": "Bearer {api_key}",
    "Content-Type": "application/json"
}}
data = {body or {}}

response = requests.{method.lower()}(url, headers=headers, json=data)

print(response.status_code)
print(response.json())"""

    elif language.lower() == "java":
        return f"""import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Scanner;

public class AgentIntegration {{
    public static void main(String[] args) {{
        try {{
            URL url = new URL("{url}");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("{method.upper()}");
            conn.setRequestProperty("Authorization", "Bearer {api_key}");
            conn.setRequestProperty("Content-Type", "application/json");

            int responseCode = conn.getResponseCode();
            if (responseCode == 200) {{
                Scanner sc = new Scanner(conn.getInputStream());
                while (sc.hasNext()) {{
                    System.out.println(sc.nextLine());
                }}
                sc.close();
            }} else {{
                System.out.println("Failed with status code: " + responseCode);
            }}
        }} catch (Exception e) {{
            e.printStackTrace();
        }}
    }}
}}"""

    elif language.lower() == "javascript":
        return f"""const fetch = require('node-fetch');

const url = "{url}";
const headers = {{
  "Authorization": "Bearer {api_key}",
  "Content-Type": "application/json"
}};
const data = {body or {}};

fetch(url, {{ method: "{method.upper()}", headers, body: JSON.stringify(data) }})
  .then(response => response.json())
  .then(data => console.log("Success:", data))
  .catch(error => console.error("Error:", error));"""

    elif language.lower() == "c++":
        return f"""#include <iostream>
#include <curl/curl.h>

int main() {{
    CURL *curl;
    CURLcode res;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if(curl) {{
        struct curl_slist *headers = NULL;
        headers = curl_slist_append(headers, "Authorization: Bearer {api_key}");
        headers = curl_slist_append(headers, "Content-Type: application/json");

        curl_easy_setopt(curl, CURLOPT_URL, "{url}");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);

        res = curl_easy_perform(curl);
        if(res != CURLE_OK)
            std::cerr << "Request failed: " << curl_easy_strerror(res) << std::endl;

        curl_easy_cleanup(curl);
    }}
    curl_global_cleanup();
    return 0;
}}"""

    return "Language not supported"
