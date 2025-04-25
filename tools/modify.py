from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from utils.blob_functions import get_all_files_from_folder, extract_text_from_blob_docx, extract_text_from_blob_pdf, connect_to_blob_storage
from utils.contract_utils import upload_contract_to_blob
from docx import Document
from io import BytesIO

@tool
def modify_contract_tool(user_id: str, contract_id: str, modification: str) -> str:
    """
    Modifies a contract by editing, adding, or removing content using an LLM.
    Fetches the latest contract from Azure Blob Storage, applies the modification, and saves the updated contract.
    Use this for requests to edit, add, or remove contract content (e.g., 'Change payment terms to CAD $200/hour', 'Add a confidentiality clause', 'Remove the insurance requirement').
    The user_id is included for future extensibility but not used in the current folder path.
    """
    print(contract_id)
    try:
        print(f"modify_contract_tool called with contract_id: {contract_id}")
        # Initialize LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        
        # Fetch the latest contract file from Azure Blob Storage
        folder_path = f"contracts/{contract_id}_"
        print(f"Searching for files in: {folder_path}")
        files = get_all_files_from_folder(folder_path)
        print(f"Files found: {files}")
        
        if not files:
            return f"No contracts found in folder: {folder_path}"

        matching_files = [file for file in files if contract_id in file]
        if not matching_files:
            return f"No contracts found matching contract_id: {contract_id}"

        container_client = connect_to_blob_storage()
        file_metadata = []
        for file in matching_files:
            blob_client = container_client.get_blob_client(file)
            properties = blob_client.get_blob_properties()
            creation_time = properties.creation_time
            file_metadata.append((file, creation_time))
        
        latest_file = max(file_metadata, key=lambda x: x[1])[0]
        print(f"Selected latest file: {latest_file}")

        # Extract text based on file type
        if latest_file.lower().endswith('.docx'):
            contract_text = extract_text_from_blob_docx(latest_file)
        elif latest_file.lower().endswith('.pdf'):
            contract_text = extract_text_from_blob_pdf(latest_file)
        else:
            return "Unsupported file type. Only .docx and .pdf are supported."

        if not contract_text or contract_text.startswith("Error"):
            return f"Failed to extract text from {latest_file}: {contract_text}"
        
        # Prepare LLM prompt for modification
        modify_prompt = """
        You are a contract modification assistant. Use the provided contract text and user instruction to intelligently modify the contract:
        - For edits, update the specified clause or term contextually, preserving the contract's style.
        - For additions, draft a new clause in legal language that fits seamlessly with the contract.
        - For removals, delete the specified clause or term while maintaining coherence.
        - Ensure all changes align with the contract's intent and formatting.
        - Return only the modified contract text.
        
        Contract text:
        {contract_text}
        
        Modification instruction:
        {modification}
        """
        
        # Call LLM to generate modified contract text
        messages = [
            {"role": "system", "content": modify_prompt.format(contract_text=contract_text, modification=modification)},
            {"role": "user", "content": modification}
        ]
        response = llm.invoke(messages)
        
        if not hasattr(response, "content") or not isinstance(response.content, str):
            return print("Error: Invalid response from LLM.")
        
        modified_text = response.content.strip()
        if not modified_text:
            return print("Error: LLM returned empty modified text.")
        
        print("saving modified to blob")
        # Save modified contract to Azure with version suffix
        upload_contract_to_blob(modified_text, "modify", contract_id)

        return modified_text
        

    except Exception as e:
        print(f"Error modifying contract: {str(e)}")
        return f"Error modifying contract: {str(e)}"