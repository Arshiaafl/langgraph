from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Optional
from tools.query import query_contract_tool

@tool
def summarize_contract_tool(user_id: str, contract_id: str, word_limit: Optional[int] = 200) -> str:
    """
    Summarizes the latest contract from Azure Blob Storage into a concise overview of key terms and provisions.
    Use this when the user requests a summary (e.g., 'Summarize the contract' or 'Give me a brief overview').
    The optional word_limit parameter specifies the maximum length of the summary (default: 200 words).
    The user_id is included for future extensibility but not used in the current folder path.
    """
    try:
        contract_text = query_contract_tool.invoke({"user_id": user_id, "contract_id": contract_id})
        if not isinstance(contract_text, str) or contract_text.startswith("Error") or "No contracts found" in contract_text:
            return contract_text

        system_prompt = (
            "You are a contract analysis assistant. Summarize the provided contract text into a concise overview, highlighting key terms (e.g., parties, duration, obligations, payments) in a clear and neutral tone.\n"
            f"Keep the summary under {word_limit} words unless otherwise specified.\n"
            "Do not include detailed analysis or risk assessment unless explicitly requested."
        )
        user_prompt = f"Contract text:\n{contract_text}\n\nSummarize the contract."
        
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
        print(f"Error summarizing contract: {str(e)}")
        return f"Error summarizing contract: {str(e)}"