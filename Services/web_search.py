import re
from urllib.parse import unquote
from html import unescape
import orjson

from curl_cffi import requests as curl_requests

# --- Global Session ---
asession = curl_requests.Session(impersonate="chrome", allow_redirects=False)
asession.headers["Referer"] = "https://duckduckgo.com/"

query_result = None


# --- Core request handler ---
def _get_url(method: str, url: str, data=None, params=None):
    try:
        resp = asession.request(method, url, data=data, params=params)
        if resp.status_code == 200:
            return resp.content
        if resp.status_code in (202, 301, 403):
            raise Exception(f"Error: {resp.status_code} rate limit error")
        if not resp:
            return None
    except Exception as error:
        if "timeout" in str(error).lower():
            raise TimeoutError("DuckDuckGo timed out error")
        raise


# --- Utility extractors ---
def extract_vqd(html_bytes: bytes) -> str:
    patterns = [(b'vqd="', 5, b'"'), (b"vqd=", 4, b"&"), (b"vqd='", 5, b"'")]
    for start_pattern, offset, end_pattern in patterns:
        try:
            start = html_bytes.index(start_pattern) + offset
            end = html_bytes.index(end_pattern, start)
            return html_bytes[start:end].decode()
        except ValueError:
            continue
    raise ValueError("Failed to extract vqd token from DuckDuckGo response")


def text_extract_json(html_bytes: bytes):
    try:
        start = html_bytes.index(b"DDG.pageLayout.load('d',") + 24
        end = html_bytes.index(b");DDG.duckbar.load(", start)
        return orjson.loads(html_bytes[start:end])
    except Exception as ex:
        print(f"Error extracting JSON: {type(ex).__name__}: {ex}")
        return []


def normalize_url(url: str) -> str:
    return unquote(url.replace(" ", "+")) if url else ""


def normalize(raw_html: str) -> str:
    return unescape(re.sub("<.*?>", "", raw_html)) if raw_html else ""


# --- Main logic ---
def duck(query: str):
    """Perform a raw DuckDuckGo search request and store results."""
    global query_result

    # Step 1: Initial POST to get vqd
    resp = _get_url("POST", "https://duckduckgo.com/", data={"q": query})
    vqd = extract_vqd(resp)

    # Step 2: Request results JSON
    params = {"q": query, "kl": "en-us", "p": "1", "s": "0", "df": "", "vqd": vqd, "ex": ""}
    resp = _get_url("GET", "https://links.duckduckgo.com/d.js", params=params)
    page_data = text_extract_json(resp)

    # Step 3: Parse and store results
    results = []
    for row in page_data:
        href = row.get("u")
        if href and href != f"http://www.google.com/search?q={query}":
            body = normalize(row.get("a", ""))
            if body:
                result = {
                    "title": normalize(row.get("t", "")),
                    "href": normalize_url(href),
                    "body": body,
                }
                results.append(result)

    query_result = results
    return results


def search(query: str):
    """Simple alias for duck()."""
    return duck(query)


def get_first_link() -> str | None:
    """Return the first result link."""
    global query_result
    if query_result and len(query_result) > 0:
        return query_result[0]["href"]
    return None

'''
# --- Example Usage ---
if __name__ == "__main__":
    print("Searching DuckDuckGo...")
    search("LangChain Gemini API integration")
    first_link = get_first_link()
    print("First Link:", first_link)
'''