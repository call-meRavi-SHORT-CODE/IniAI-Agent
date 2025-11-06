from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re




GOOGLE_API_KEY = "AIzaSyAnPL4zvdny1jVeaikGJZz4JDL_5q11aSA"


planner_prompt = """
You are IniAI, an AI Software Engineer Agent.

The user has asked: {{ prompt }}

Your task is to generate a clear, step-by-step plan to achieve the user’s goal.


``
Follow this exact response structure:

Project Name: <Give a short, relevant project title — no longer than 5 words>

Your Reply to the Human Prompter: <Provide a brief, natural response explaining that you’re creating the plan — avoid starting with “As an AI”.>

Current Focus: <State the main goal or objective of the plan.>

Plan:

 Step 1: Explain the first concrete action required to move toward the goal.

 Step 2: Explain the next key action or step.
...

 Step N: Explain the final step needed to complete the task.

Summary: <Provide a concise wrap-up of the plan, noting any important dependencies, key factors, or possible challenges.>
``

Each step must be specific, actionable, and easy to understand. The plan should comprehensively address the user’s request — from research and development to testing and reporting.
Assume you have access to a web browser and search tools to complete your work.
After outlining the steps, summarize the plan, emphasizing important dependencies or potential obstacles.
Keep the plan appropriately detailed — simple tasks may only need one or two concise steps. Avoid overcomplicating straightforward requests.
Your output must follow the code block format shown above exactly. Any other response format will be rejected.

Example:

Project Name: Weather Forecast Dashboard

Your Reply to the Human Prompter: Sure! Let’s create a plan to build a weather dashboard that displays real-time data.

Current Focus: Develop a responsive web app to show current and forecasted weather information.

Plan:

 Step 1: Research public weather APIs (e.g., OpenWeatherMap) and review API documentation.

 Step 2: Set up a Flask backend to handle API requests and process weather data.

 Step 3: Design a simple, dark-themed HTML/CSS interface to display temperature, humidity, and weather icons.

 Step 4: Integrate the backend with the frontend to fetch and display live weather updates.

 Step 5: Test the dashboard for various cities and ensure data updates correctly.

 Step 6: Deploy the application on a cloud platform (e.g., Render, netlify).

Summary: This plan focuses on building a live weather dashboard using Flask and public APIs. Key challenges include API rate limits and ensuring responsive UI updates.


"""





llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)

# --- Create prompt template ---
prompt = ChatPromptTemplate.from_messages([
    ("system", planner_prompt),
    ("user", "Request: {user_prompt}")
])

# --- Output parser ---
parser = StrOutputParser()

# --- Create full chain ---
chain = prompt | llm | parser


# --- Function to execute ---
def execute(user_prompt: str) -> str:
    """Run the planner chain"""
    return chain.invoke({"user_prompt": user_prompt})


# --- Function to parse response ---
def parse_response(response: str):
    result = {
        "project": "",
        "reply": "",
        "focus": "",
        "plans": {},
        "summary": ""
    }

    current_section = None
    current_step = None

    for line in response.split("\n"):
        line = line.strip()

        if line.startswith("Project Name:"):
            current_section = "project"
            result["project"] = line.split(":", 1)[1].strip()
        elif line.startswith("Your Reply to the Human Prompter:"):
            current_section = "reply"
            result["reply"] = line.split(":", 1)[1].strip()
        elif line.startswith("Current Focus:"):
            current_section = "focus"
            result["focus"] = line.split(":", 1)[1].strip()
        elif line.startswith("Plan:"):
            current_section = "plans"
        elif line.startswith("Summary:"):
            current_section = "summary"
            result["summary"] = line.split(":", 1)[1].strip()
        elif current_section == "reply":
            result["reply"] += " " + line
        elif current_section == "focus":
            result["focus"] += " " + line
        elif current_section == "plans":
            match = re.match(r"(?:- \[ \] )?Step\s*(\d+):\s*(.*)", line)
            if match:
                current_step = int(match.group(1))
                step_text = match.group(2).strip()
                result["plans"][current_step] = step_text
            elif current_step:
                result["plans"][current_step] += " " + line
        elif current_section == "summary":
            result["summary"] += " " + line.replace("```", "")

    # Clean up whitespace
    for key in result:
        if isinstance(result[key], str):
            result[key] = result[key].strip()

    return result


# --- Run the agent directly ---
if __name__ == "__main__":
    user_prompt = "Create me a todo app using python"

    response = execute(user_prompt)
    print("\nRaw Response:\n", response)

    parsed = parse_response(response)
    print("\nParsed Output:\n", parsed)