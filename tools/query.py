from langchain_core.tools import tool
from utils.blob_functions import get_all_files_from_folder, extract_text_from_blob_docx, extract_text_from_blob_pdf, connect_to_blob_storage

@tool
def query_contract_tool(user_id: str, contract_id: str) -> str:
    """
    Fetches the latest contract text from Azure Blob Storage for the given contract_id and answers a specific question about it.
    Use this when the user asks a targeted question (e.g., 'What is the expiration date?').
    The user_id is included for future extensibility but not used in the current folder path.
    """
    try:
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

        if latest_file.lower().endswith('.docx'):
            text = extract_text_from_blob_docx(latest_file)
        elif latest_file.lower().endswith('.pdf'):
            text = extract_text_from_blob_pdf(latest_file)
        else:
            return "Unsupported file type. Only .docx and .pdf are supported."

        if not text or text.startswith("Error"):
            return f"Failed to extract text from {latest_file}: {text}"
        
        return text
    except Exception as e:
        print(f"Error fetching contract: {str(e)}")
        return f"Error fetching contract: {str(e)}"