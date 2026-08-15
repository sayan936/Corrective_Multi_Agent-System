import os
from typing import Literal,TypedDict
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic


load_dotenv()

MODEL_GROQ = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
MODEL_ANTHROPIC = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

MAX_REVISIONS = int(os.getenv("MAX_REVISIONS", 5)) 


model_groq =  ChatGroq(
    model = MODEL_GROQ,
    api_key = os.getenv("GROQ_API_KEY"),    
    temperature = 0
)

model_anthropic = ChatAnthropic(
    model = MODEL_ANTHROPIC,
    api_key = os.getenv("ANTHROPIC_API_KEY"),
    temperature = 0
)


class ReviewResult(BaseModel):
    decision: Literal["PASS", "REVISE"] = Field(
        description="The decision made by the model, either 'PASS' or 'REVISE'."
    )
    feedback: str = Field(
        description="Short feedback provided by the model regarding the decision.Empty string if the decision is PASS"
    )


review_model = model_groq.with_structured_output(ReviewResult)


class State(TypedDict):
    topic:str
    draft:str
    feedback:str
    decision: str
    revision_count: str 



def writer(state:State): 
    """Agent 1: create the first answer based on the topic"""
    response = model_anthropic.invoke(
        [
            {
                "role": "system",
                "content": (
                    "You are a beginner-friendly teacher. Explain the topic in 120-160 words. "
                    "Use simple language, one everyday analogy, and one tiny example."
                ),
            },
            {"role": "user", "content": f"Explain: {state['topic']}"},
        ]
    )
    return{
        "draft": response.content,
        "feedback": "",
        "decision": "",
        "revision_count": 0
    }

def reviewer(state:State):
    """Agent 2: evaluate the current answer."""
    review = review_model.invoke(
        [
            {
                "role": "system",
                "content": (
                    "You are a strict reviewer. Check the answer using ONLY these rules:\n"
                    "1. It is easy for a beginner.\n"
                    "2. It contains an everyday analogy.\n"
                    "3. It contains a tiny concrete example.\n"
                    "4. It stays focused on the requested topic.\n"
                    "If any rule fails, choose REVISE and give one or two precise improvements."
                ),
            },
            {
                "role": "user",
                "content": f"Topic: {state['topic']}\n\nAnswer:\n{state['draft']}",
            },
        ]
    )
    return {"decision": review.decision, "feedback": review.feedback}

def reviser(state: State):
    """Agent 3: improve the answer using reviewer feedback."""
    response = model_anthropic.invoke(
        [
            {
                "role": "system",
                "content": (
                    "You are a reviser. Improve the answer using the reviewer feedback. "
                    "Keep it beginner-friendly and concise. Return only the improved answer."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {state['topic']}\n\n"
                    f"Current answer:\n{state['draft']}\n\n"
                    f"Reviewer feedback:\n{state['feedback']}"
                ),
            },
        ]
    )
    return {
        "draft": response.content,
        "revision_count": state["revision_count"] + 1,
    }


def route_after_review(state: State):
    """Route to either end or revision based on the review decision."""
    if state["decision"] == "PASS":
        return "done"
    elif  state["revision_count"] >= MAX_REVISIONS:
        return "done"
    else:
        return "revise"


builder = StateGraph(State)
builder.add_node("write", writer)
builder.add_node("review", reviewer)
builder.add_node("revise", reviser)

builder.add_edge(START, "write")
builder.add_edge("write", "review")
builder.add_conditional_edges(
    "review",
    route_after_review,
    {
        "revise": "revise",
         "done": END,
    }
)
builder.add_edge("revise", "review")

graph = builder.compile()

def run_workflow(topic:str):
    initial_state = {
        "topic": topic,
        "draft": "",
        "feedback": "",
        "decision": "",
        "revision_count": 0
    }
    final_state = initial_state.copy()
    events = [] 

    for update in graph.stream(initial_state,stream_mode ="updates"):
        for node_name, values in update.items():
           final_state.update(values)
           events.append(
               {
               "agent":node_name,
               "draft":  values.get("draft", ""),
               "decision": values.get("decision", ""),
                "feedback": values.get("feedback", ""),
                "revision_count": final_state["revision_count"]
           }
        )
    return {
        "topic": topic,
        "events": events,  
        "final_answer": final_state["draft"],
        "final_decision": final_state["decision"],
        "total_revisions": final_state["revision_count"],
         "provider": "Groq",
        "model": MODEL_GROQ,
    }


def run_demo(topic: str):
    """Small CLI version, useful if you want to demo without the browser."""
    result = run_workflow(topic)

    for event in result["events"]:
        print(event)
        print("*******************")

    # print("\n=== SELF-CORRECTING MULTI-AGENT DEMO ===")
    # print(f"Provider: {result['provider']}")
    # print(f"Model: {result['model']}")
    # print(f"Topic: {topic}\n")

    # for event in result["events"]:
    #     print(f"\n--- {event['agent'].upper()} ---")
    #     if event["agent"] in {"writer", "reviser"}:
    #         print(event["draft"])
    #     elif event["agent"] == "reviewer":
    #         print("Decision:", event["decision"])
    #         print("Feedback:", event["feedback"] or "No changes needed")

    # print("\n=== FINAL ANSWER ===")
    # print(result["final_answer"])
    # print(f"\nFinal decision: {result['final_decision']}")
    # print(f"Revisions used: {result['total_revisions']}")


if __name__ == "__main__":
    topic = input("Enter a topic (example: What is an AI agent?): ").strip()
    if not topic:
        topic = "What is an AI agent?"
    run_demo(topic)