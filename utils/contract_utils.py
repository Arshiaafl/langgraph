from utils.blob_functions import get_all_files_from_folder, save_text_output_to_blob

def upload_contract_to_blob(text: str, action: str, user_id: str):
    try:
        prefix = f"contracts/{user_id}_"
        files = get_all_files_from_folder(prefix)
        versions = [f for f in files if "contract_v" in f]

        version_numbers = []
        for v in versions:
            try:
                version = int(v.split("_v")[1].split(".")[0])
                version_numbers.append(version)
            except (IndexError, ValueError):
                continue

        latest_version = max(version_numbers, default=0)
        new_version = latest_version + 1
    except Exception as e:
        print(f"Versioning error: {e}")
        new_version = 1

    if action == "finalized":
        docx_filename = f"contracts/{user_id}_{action}_contract_latest.docx"
        pdf_filename = f"contracts/{user_id}_{action}_contract_latest.pdf"
    else:
        docx_filename = f"contracts/{user_id}_{action}_contract_v{new_version}.docx"
        pdf_filename = f"contracts/{user_id}_{action}_contract_v{new_version}.pdf"
    return save_text_output_to_blob(text, docx_filename, pdf_filename)