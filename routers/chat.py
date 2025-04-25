from fastapi import APIRouter, Depends, HTTPException
from models.schemas import ChatRequest
from dependencies.openai_client import get_openai_client
from agents.contract_agent import contract_agent_graph
from openai import OpenAI

router = APIRouter()

@router.post("/chat", response_model=None)
async def chat(
    user_id: str,
    contract_id: str,
    organization_id: str,
    request: ChatRequest,
    client: OpenAI = Depends(get_openai_client)
):
    """
    Chat endpoint to query contracts using a LangGraph agent.
    Requires user_id, contract_id, organization_id as query parameters and prompt in JSON body.
    """
    try:
        # Initialize state for LangGraph
        initial_state = {
            "user_id": user_id,
            "contract_id": contract_id,
            "prompt": request.prompt,
            "contract_text": "",
            "response": "",
            "history": []
        }

        # Run the LangGraph workflow
        result = contract_agent_graph.invoke(initial_state)

        # Extract response
        response_text = result["response"]
        if response_text.startswith("Error"):
            raise HTTPException(status_code=500, detail=response_text)

        return {
            "result": response_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")