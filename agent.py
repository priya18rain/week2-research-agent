import requests
from openai import OpenAI
from dotenv import load_dotenv
import os
import json


import trafilatura
from urllib.parse import urlparse

load_dotenv()

SERPER_API_KEY = os.environ["SERPER_API_KEY"]

def web_search(query: str, num_results: int = 5) -> list[dict]:
    """Search the web. Returns a list of {title, link, snippet} dicts."""
    response = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
        json={"q": query, "num": num_results},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("organic", []):
        results.append({
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        })
    return results



MAX_CHARS = 3000
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}


def web_fetch(url):
    # try llms.txt first
    try:
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        resp = requests.get(f"{base}/llms.txt", headers=HEADERS, timeout=5)
        if resp.status_code == 200 and resp.text.strip():
            content = resp.text
            if len(content) > MAX_CHARS:
                content = content[:MAX_CHARS] + "\n\n[...truncated]"
            return content
    except Exception:
        pass

    # normal fetch
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        return f"Error fetching {url}: {e}"
    text = trafilatura.extract(response.text)
    if not text:
        return "No content found."
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n\n[...truncated]"
    return text

search_tool = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information. Use this when the user asks "
            "about recent events, specific facts, or anything you are uncertain about. "
            "Returns a list of search results with titles, URLs, and snippets."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Be specific and targeted.",
                }
            },
            "required": ["query"],
        },
    },
}

fetch_tool = {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": (
            "Fetch and read the full content of a web page. Use this after web_search "
            "to read a specific result in detail. Prefer this for documentation, articles, "
            "and pages where the snippet is not enough."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to fetch, including https://",
                }
            },
            "required": ["url"],
        },
    },
}

tools = [
    search_tool,
    fetch_tool
]

def dispatch(tool_call):

    name = tool_call.function.name
    arguments = json.loads(
        tool_call.function.arguments
    )
    if name == "web_search":
        return json.dumps(
            web_search(**arguments)
        )
    if name == "web_fetch":
        return web_fetch(**arguments)
    return f"Unknown tool: {name}"
    
SYSTEM_PROMPT = """You are a research assistant that answers questions by searching the web and reading sources in full before responding.

Process:
1. Use web_search to find relevant pages for the question. Use specific, targeted queries.
2. Use web_fetch to read the full content of the most promising results — search snippets are often too short to be useful.
3. Once you have enough information, synthesize a clear, direct answer.

Guidelines:
- Always cite sources by including the URL next to the claim it supports.
- If sources disagree, note the disagreement rather than picking one arbitrarily.
- Don't fetch more pages than necessary — 2-4 fetches is usually enough for a focused question.
- If a fetch fails or returns no content, try a different source rather than giving up.
- If you can't find a clear answer after reasonable effort, say so honestly rather than guessing.
- Keep the final answer concise and well-organized; don't pad it with unnecessary preamble.
- Base answers only on tool results.
- Do not add facts that are not present in tool outputs.
- If information is missing, say it is missing.
- Always cite the source URL used.
"""

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)

def run_agent(messages):
    
    for _ in range(5):
        response = client.chat.completions.create(
            model="openrouter/free",
            messages=messages,
            tools=tools
        )
        message = response.choices[0].message
        
        if not message.tool_calls:
            return message.content
        messages.append(message.model_dump(exclude_none=True))
        for tool_call in message.tool_calls:
            
            try:
                result = dispatch(tool_call)
            except Exception as e:
                result = f"Error: {e}"

            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
    return "Iteration limit reached"

