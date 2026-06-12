# prompt_server.py
from fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("EssayWritingPrompts")

@mcp.prompt()
def plan_prompt(task: str) -> str:
    """Generate high-level outline for a given essay task."""
    return (
        f"You are an expert writer tasked with writing a high level outline of an essay. "
        f"Write such an outline for the user provided topic: {task}. Give an outline of "
        f"the essay along with any relevant notes or instructions for the sections."
    )

@mcp.prompt()
def writer_prompt(content: str) -> str:
    """Writer prompt with gathered RAG & web search context."""
    return (
        f"You are an essay assistant tasked with writing excellent 5-paragraph essays. "
        f"Generate the best essay possible for the user's request and the initial outline. "
        f"If the user provides critique, respond with a revised version of your previous attempts. "
        f"Utilize all the information below as needed:\n\n"
        f"------\n\n"
        f"{content}"
    )

@mcp.prompt()
def reflection_prompt(draft: str) -> str:
    """Teacher grading and evaluation feedback prompt."""
    return (
        f"You are a teacher grading an essay submission. Generate critique and recommendations "
        f"for the user's submission: {draft}\n\n"
        f"Provide detailed recommendations, including requests for length, depth, style, etc."
    )

@mcp.prompt()
def research_plan_prompt(task: str) -> str:
    """Query generator for the initial planning phase."""
    return (
        f"You are a researcher charged with providing information that can be used when writing "
        f"the following essay: {task}. Generate a list of search queries that will gather "
        f"any relevant information. Only generate 3 queries max."
    )

@mcp.prompt()
def research_critique_prompt(critique: str) -> str:
    """Query generator based on teacher critique and feedback."""
    return (
        f"You are a researcher charged with providing information that can be used when making "
        f"any requested revisions (as outlined below):\n\n"
        f"{critique}\n\n"
        f"Generate a list of search queries that will gather any relevant information. Only generate 3 queries max."
    )

if __name__ == "__main__":
    mcp.run()