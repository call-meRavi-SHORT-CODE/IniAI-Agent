import sys
import time
import json
from functools import wraps




def retry_wrapper(func):
    """Retries a function up to 5 times if it returns a falsy result."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        max_tries = 5
        for attempt in range(1, max_tries + 1):
            result = func(*args, **kwargs)
            if result:
                return result

            warning_msg = f"Invalid response from model, retrying attempt {attempt}/{max_tries}..."
            print(warning_msg)
            #emit_agent("info", {"type": "warning", "message": warning_msg})

            time.sleep(2)

        error_msg = "Maximum 5 attempts reached. The model keeps failing. Try another model."
        print(error_msg)
        #emit_agent("info", {"type": "error", "message": error_msg})

        # Instead of exiting directly, return False for controlled flow
        return False

    return wrapper


class InvalidResponseError(Exception):
    """Raised when LLM response can't be parsed as JSON."""
    pass


def validate_responses(func):
    """
    Decorator that tries multiple strategies to parse an LLM response into JSON.

    It supports:
    - Direct JSON
    - JSON inside triple backticks
    - JSON substring extraction
    - JSON line-by-line parsing
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if len(args) < 2:
            raise ValueError("validate_responses decorator expects response as the second argument")

        # Convert args tuple to list for safe mutation
        args = list(args)
        raw_response = str(args[1]).strip()

        # 1️⃣ Direct JSON
        try:
            response = json.loads(raw_response)
            args[1] = response
            return func(*args, **kwargs)
        except json.JSONDecodeError:
            pass

        # 2️⃣ JSON enclosed in triple backticks
        try:
            extracted = raw_response.split("```")[1].strip()
            response = json.loads(extracted)
            args[1] = response
            return func(*args, **kwargs)
        except (IndexError, json.JSONDecodeError):
            pass

        # 3️⃣ Extract JSON substring between {...}
        try:
            start = raw_response.find("{")
            end = raw_response.rfind("}")
            if start != -1 and end != -1:
                extracted = raw_response[start:end + 1]
                response = json.loads(extracted)
                args[1] = response
                return func(*args, **kwargs)
        except json.JSONDecodeError:
            pass

        # 4️⃣ Line-by-line JSON check
        for line in raw_response.splitlines():
            try:
                response = json.loads(line.strip())
                args[1] = response
                return func(*args, **kwargs)
            except json.JSONDecodeError:
                continue

        # If all parsing attempts fail
        #emit_agent("info", {"type": "error", "message": "Failed to parse response as JSON"})
        print("❌ Failed to parse response as JSON.")
        return False

    return wrapper
