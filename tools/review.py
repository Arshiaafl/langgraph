from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Optional
from tools.query import query_contract_tool

@tool
def review_contract_tool(user_id: str, contract_id: str, focus: Optional[str] = None) -> str:
    """
    Reviews the latest contract from Azure Blob Storage, identifying key clauses, potential risks, and providing a summary.
    Use this when the user requests a detailed review or analysis (e.g., 'Review the contract' or 'Analyze payment terms').
    The optional focus parameter targets specific aspects (e.g., payment terms).
    The user_id is included for future extensibility but not used in the current folder path.
    """
    try:
        contract_text = query_contract_tool.invoke({"user_id": user_id, "contract_id": contract_id})
        if not isinstance(contract_text, str) or contract_text.startswith("Error") or "No contracts found" in contract_text:
            return contract_text

        system_prompt = (
            "You are a contract analysis assistant. Review the provided contract text and provide a concise analysis, including:\n"
            "- Key clauses (e.g., effective date, termination, payment terms, obligations).\n"
            "- Potential risks (e.g., ambiguous terms, missing clauses, legal issues).\n"
            "- A brief summary of findings.\n"
            "If a specific focus is provided (e.g., payment terms), prioritize that aspect in the analysis.\n"
            "Format the response clearly, using bullet points for clauses and risks."
        )
        user_prompt = f"Contract text:\n{contract_text}\n\nReview the contract."
        if focus:
            user_prompt += f" Focus on: {focus}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        response = llm.invoke(messages)
        if not hasattr(response, "content") or not isinstance(response.content, str):
            return "Error: Invalid response from LLM."
        
        return response.content
    except Exception as e:
        print(f"Error reviewing contract: {str(e)}")
        return f"Error reviewing contract: {str(e)}"