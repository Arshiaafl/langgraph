from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated
from tools.query import query_contract_tool
from tools.review import review_contract_tool
from tools.summarize import summarize_contract_tool
from tools.modify import modify_contract_tool
from prompts.contract_system_prompt import SYSTEM_PROMPT
import re

class AgentState(TypedDict):
    user_id: str
    contract_id: str
    prompt: str
    contract_text: str
    response: str
    history: list[dict]

llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools([query_contract_tool, review_contract_tool, summarize_contract_tool, modify_contract_tool])

def router_node(state: AgentState) -> dict:
    state["history"].append({"role": "user", "content": state["prompt"]})
    return state

def contract_agent_node(state: AgentState) -> AgentState:
    try:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": state["prompt"]}
        ]
        response = llm.invoke(messages)
        
        response_parts = []
        tool_names = []
        contract_text = None

        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                print(f"Selected tool: {tool_name}, Args: {tool_args}")
                tool_names.append(tool_name)

                if tool_name == "query_contract_tool":
                    if contract_text is None:
                        contract_text = query_contract_tool.invoke(tool_args)
                        if not isinstance(contract_text, str) or contract_text.startswith("Error") or "No contracts found" in contract_text:
                            response_parts.append(contract_text)
                            continue
                    state["contract_text"] = contract_text
                    query_prompt = (
                        "Use the provided contract text to answer the user's query accurately. "
                        "If the information is not in the contract, say so. Provide concise answers."
                    )
                    query_messages = [
                        {"role": "system", "content": query_prompt},
                        {"role": "user", "content": f"Contract text:\n{contract_text}\n\nQuery: {state['prompt']}"}
                    ]
                    query_response = llm.invoke(query_messages)
                    response_parts.append(query_response.content if hasattr(query_response, "content") else "Error: Invalid LLM response.")
                elif tool_name == "review_contract_tool":
                    response_parts.append(review_contract_tool(tool_args))
                elif tool_name == "summarize_contract_tool":
                    response_parts.append(summarize_contract_tool(tool_args))
                elif tool_name == "modify_contract_tool":
                    response_parts.append(modify_contract_tool.invoke(tool_args))
                else:
                    response_parts.append(f"Error: Unknown tool {tool_name}")

        # Fallback for missed queries
        if "query_contract_tool" not in tool_names:
            query_patterns = [
                r"tell me.*?\b(termination|duration|expiration|payment|conditions)\b",
                r"what (is|are).*?\b(termination|duration|expiration|payment|conditions)\b",
                r"how long"
            ]
            prompt_lower = state["prompt"].lower()
            for pattern in query_patterns:
                if re.search(pattern, prompt_lower):
                    print("Fallback: Detected missed query, invoking query_contract_tool")
                    if contract_text is None:
                        contract_text = query_contract_tool.invoke({
                            "user_id": state["user_id"],
                            "contract_id": state["contract_id"]
                        })
                        if not isinstance(contract_text, str) or contract_text.startswith("Error") or "No contracts found" in contract_text:
                            response_parts.append(contract_text)
                            break
                    state["contract_text"] = contract_text
                    query_prompt = (
                        "Use the provided contract text to answer the user's query accurately. "
                        "If the information is not in the contract, say so. Provide concise answers."
                    )
                    query_messages = [
                        {"role": "system", "content": query_prompt},
                        {"role": "user", "content": f"Contract text:\n{contract_text}\n\nQuery: {state['prompt']}"}
                    ]
                    query_response = llm.invoke(query_messages)
                    response_parts.append(query_response.content if hasattr(query_response, "content") else "Error: Invalid LLM response.")
                    break

        # Combine response parts with clear headings
        formatted_parts = []
        for tool_name, part in zip(tool_names, response_parts):
            if part and not part.startswith("Error"):
                if tool_name == "summarize_contract_tool":
                    formatted_parts.append(f"**Summary**:\n{part}")
                elif tool_name == "review_contract_tool":
                    formatted_parts.append(f"**Review**:\n{part}")
                elif tool_name == "query_contract_tool":
                    formatted_parts.append(f"**Query Response**:\n{part}")
                elif tool_name == "modify_contract_tool":
                    formatted_parts.append(f"**Modification**:\n{part}")

        state["response"] = "\n\n".join(formatted_parts)
        if not state["response"]:
            state["response"] = "Error: No valid responses from tools."
        state["contract_text"] = contract_text if contract_text else ""

        state["history"].append({"role": "assistant", "content": state["response"]})
        return state
    except Exception as e:
        print(f"Error processing query: {str(e)}")
        state["response"] = f"Error processing query: {str(e)}"
        state["contract_text"] = ""
        return state

def create_contract_agent_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("router", router_node)
    workflow.add_node("contract_agent", contract_agent_node)
    workflow.set_entry_point("router")
    workflow.add_edge("router", "contract_agent")
    workflow.add_edge("contract_agent", END)
    return workflow.compile()

contract_agent_graph = create_contract_agent_graph()