import json
import time
import sys
from typing import List
from functools import wraps

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

from Services.utils import retry_wrapper, validate_responses
from Services.web_search import DuckDuckGoSearch

GOOGLE_API_KEY = "AIzaSyAnPL4zvdny1jVeaikGJZz4JDL_5q11aSA"

researcher_prompt = """
Your task is to act as a Research Agent that generates optimized web search queries.

You are given a step-by-step plan. For each step, write the most effective search queries to collect additional information from the web — only if that information is not already known to your base model.

Craft precise, well-optimized Google-style queries using relevant keywords and phrases to ensure you find the most accurate and specific results (you’ll be clicking the first link).

If no additional information is needed for a step, leave the "queries" field empty. Only ask the user for clarification when absolutely necessary.

Step-by-Step Plan:
{{ step_by_step_plan }}

Respond strictly in the following JSON format:

{
"queries": ["<QUERY 1>", "<QUERY 2>", "<QUERY 3>", ...],
"ask_user": "<QUESTION FOR USER IF NEEDED, OTHERWISE EMPTY STRING>"
}

makefile
Copy code

Example:
{
"queries": ["Using Bing Search API in Python", "Claude API Python documentation"],
"ask_user": "Could you please provide API keys for Claude, OpenAI, and Firebase?"
}



Keywords for Search Optimization: {{ contextual_keywords }}

Guidelines:
- Generate a maximum of 3 queries only.
- Do NOT search for topics your base model already knows (e.g., how to build a Flask server in Python).
- Avoid unrelated or generic searches — stay strictly focused on the plan.
- Integrate the contextual keywords naturally into your queries for maximum relevance.
- Search only for **documentation or advanced references**, never basic tutorials.
- Forbidden topics: installation steps, setup guides, or general how-to questions.
- You may return an empty "queries" list if no search is required for any step.
- Return exactly **one JSON object** with both "queries" and "ask_user" fields — no extra text or multiple objects allowed.

Any output that doesn’t match this exact JSON structure will be rejected.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import List

from config import GOOGLE_API_KEY, researcher_prompt


# Initialize all components globally
search_engine = DuckDuckGoSearch()
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GOOGLE_API_KEY)
prompt = ChatPromptTemplate.from_messages([("system", researcher_prompt)])
parser = StrOutputParser()

# Full chain: Prompt → LLM → Parser
chain = prompt | llm | parser


@validate_responses
def validate_response(response: str) -> dict | bool:
    """Ensure response contains required fields."""
    if "queries" not in response and "ask_user" not in response:
        return False
    return {
        "queries": response["queries"],
        "ask_user": response["ask_user"]
    }


@retry_wrapper
def execute(step_by_step_plan: str, contextual_keywords: List[str], project_name: str) -> dict | bool:
    """Run the research pipeline."""
    contextual_keywords_str = ", ".join(map(lambda k: k.capitalize(), contextual_keywords))

    response = chain.invoke({
        "step_by_step_plan": step_by_step_plan,
        "contextual_keywords": contextual_keywords_str
    })

    valid_response = validate_response(response)
    return valid_response


def search_online(query: str) -> str | None:
    """Perform a DuckDuckGo search and return the first result link."""
    try:
        search_engine.search(query)
        return search_engine.get_first_link()
    except Exception as e:
        print(f"Search failed: {e}")
        return None


"""
Workflow (function-based):

execute()
↓
llm.inference() → returns raw string from Gemini
↓
validate_responses() decorator → parses string → makes dict
↓
validate_response() checks keys & cleans output
↓
returns clean, valid response dict or False
"""


if __name__ == "__main__":
    # Step-by-step plan for which you want queries generated
    step_by_step_plan = """
    1. Set up the basic project structure: Create a `todo.py` file for the main application logic and a `tasks.txt` file to store the to-do items.
    2. Implement the `add_task` function: This function should take a task description as input, append it to the `tasks.txt` file, and print a confirmation message.

    3.  Implement the `add_task` function: This function should take a task description as input, append it to the `tasks.txt` file, and print a confirmation message.
    """

    # Contextual keywords to guide query optimization
    contextual_keywords = [
    "Python",
    "File Handling",
    "To-do List",
    "Task Management",
    "Command Line App",
    "Functions",
    "File I/O",
    "Persistence",
    "Text File Storage",
    "Beginner Python Project"
]

    # Run the research pipeline
    response = execute(
        step_by_step_plan=step_by_step_plan,
        contextual_keywords=contextual_keywords,
        project_name="TestResearch"
    )

    # Print output
    print("\n=== Researcher Agent Output ===")
    print(response)
