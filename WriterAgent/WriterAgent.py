import os
from langgraph.graph import StateGraph,END
from typing import TypedDict, Annotated,List
import operator
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AnyMessage, HumanMessage,SystemMessage,ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv,find_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.utils.pydantic import BaseModel
from tavily import TavilyClient

_ = load_dotenv(find_dotenv())

openai_key = os.getenv("OPENAI_API_KEY")

memory = InMemorySaver()


## Creating the state of agent ###

class AgentState(TypedDict):
    task: str
    plan: str
    draft: str
    critique: str
    content: List[str]
    revision_number: int
    max_revisions: int


### LLM ###

model = ChatOpenAI(model = "poolside/laguna-m.1:free",
                   base_url="https://openrouter.ai/api/v1",
                   api_key=openai_key,
                   temperature=0)


##### Structure the agents prompts ############

PLAN_PROMPT = """You are an expert writer tasked with writing a high level outline of an essay. \
Write such an outline for the user provided topic. Give an outline of the essay along with any relevant notes \
or instructions for the sections."""

WRITER_PROMPT = """You are an essay assistant tasked with writing excellent 5-paragraph essays.\
Generate the best essay possible for the user's request and the initial outline. \
If the user provides critique, respond with a revised version of your previous attempts. \
Utilize all the information below as needed: 

------

{content}"""

REFLECTION_PROMPT = """You are a teacher grading an essay submission. \
Generate critique and recommendations for the user's submission. \
Provide detailed recommendations, including requests for length, depth, style, etc."""

RESEARCH_PLAN_PROMPT = """You are a researcher charged with providing information that can \
be used when writing the following essay. Generate a list of search queries that will gather \
any relevant information. Only generate 3 queries max."""

RESEARCH_CRITIQUE_PROMPT = """You are a researcher charged with providing information that can \
be used when making any requested revisions (as outlined below). \
Generate a list of search queries that will gather any relevant information. Only generate 3 queries max."""



#### Setting the format #########

class Queries(BaseModel):
    queries: List[str]


### setting the tavily search #######

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


#### AGENT PLAN ####

def plan_node(state: AgentState):
    messages = [
        SystemMessage(content=PLAN_PROMPT),
        HumanMessage(content=state['task'])
    ]

    response = model.invoke(messages)
    return {"plan": response.content}


##### AGENT RESEARCH #########
def research_plan_node(state: AgentState):
    queries = model.with_structured_output(Queries).invoke([
        SystemMessage(content=RESEARCH_PLAN_PROMPT),
        HumanMessage(content=state['task'])
    ])
    content = state['content'] or []
    print(content)
    for q in queries.queries:
        
        response = tavily.search(query=q, max_results=2)
        
        for r in response['results']:
            content.append(r['content'])
    return {"content": content}


########### AGENT GENERATION ################ APNA WRITER BHAIIIIIII  ###

def generation_node(state: AgentState):
    content = "\n\n".join(state["content"]or[])
    user_message = HumanMessage(
        content=f"{state['task']}\n\n !!!!!!!! Here is my plan !!!!!!!!!:\n\n{state['plan']}")
    messages = [
        SystemMessage(content=WRITER_PROMPT.format(content = content)),
        user_message
    ]
    response = model.invoke(messages)

    return{
        "draft":response.content,
        "revision_number": state.get("revision_number",1)+1
    }


##################  AGENT REFLECTION ##############

def reflection_node(state: AgentState):
    messages = [
        SystemMessage(content=REFLECTION_PROMPT),
        HumanMessage(content=state['draft'])
    ]
    response = model.invoke(messages)
    return {"critique": response.content}



##########  AGENT WHO RESEARCH ON CRITIQUE #########

def research_critique_node(state: AgentState):
    messages = [
        SystemMessage(content=RESEARCH_CRITIQUE_PROMPT),
        HumanMessage(content=state['critique'])
    ]
    queries = model.with_structured_output(Queries).invoke(messages)

    content = state['content'] or []

    for q in queries.queries :
        response = tavily.search(query=q,max_results=2)
        for r in response['results']:
            content.append(r['content'])
    
    return {"content": content}


######## Chekker ###########

def should_continue(state):
    if state["revision_number"] > state["max_revisions"]:
        return END
    return "reflect"


######### MANAGER #########

builder = StateGraph(AgentState)

builder.add_node("planner",plan_node)
builder.add_node("research_plan",research_plan_node)
builder.add_node("generate",generation_node)
builder.add_node("reflect",reflection_node)
builder.add_node("research_critique",research_critique_node)

builder.set_entry_point("planner")


builder.add_conditional_edges(
    "generate",
    should_continue,
    {END:END,"reflect":"reflect"}
)

builder.add_edge("planner","research_plan")
builder.add_edge("research_plan","generate")
builder.add_edge("reflect","research_critique")
builder.add_edge("research_critique","generate")

graph = builder.compile(checkpointer=memory)


thread = {"configurable": {"thread_id": "1"}}
for s in graph.stream({
    'task': "what is the difference between langchain and langsmith",
    "max_revisions": 2,
    "revision_number": 1,
    "content": []
}, thread):
    print(s)