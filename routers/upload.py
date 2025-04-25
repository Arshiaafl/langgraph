from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from dependencies.openai_client import get_openai_client
from openai import OpenAI
import PyPDF2
from docx import Document
from io import BytesIO
from utils.blob_functions import save_text_to_blob_as_docx, save_text_to_blob_as_pdf
from utils.contract_utils import upload_contract_to_blob

router = APIRouter()

@router.post("/upload")
async def upload(
    user_id: str,
    contract_id: str,
    organization_id: str,
    file: UploadFile = File(...),
    prompt: str | None = None,
    client: OpenAI = Depends(get_openai_client)
):
    """
    Upload endpoint to process a text, PDF, or DOCX file and optional prompt with OpenAI GPT-4o.
    Saves the extracted text as PDF and DOCX in Azure Blob Storage.
    Requires user_id, contract_id, organization_id as query parameters, file, and optional prompt in form-data.
    """
    try:
        # Read file content
        content = await file.read()

        # Determine file type and extract text
        if file.filename.lower().endswith('.pdf'):
            # Handle PDF files
            pdf_reader = PyPDF2.PdfReader(BytesIO(content))
            file_text = ""
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    file_text += text + "\n"
            if not file_text.strip():
                raise HTTPException(status_code=400, detail="No text could be extracted from the PDF")
        elif file.filename.lower().endswith('.docx'):
            # Handle DOCX files
            doc = Document(BytesIO(content))
            file_text = ""
            for para in doc.paragraphs:
                if para.text.strip():
                    file_text += para.text + "\n"
            if not file_text.strip():
                raise HTTPException(status_code=400, detail="No text could be extracted from the DOCX")
        else:
            # Assume text-based files
            file_text = content.decode("utf-8", errors="ignore")
            if not file_text.strip():
                raise HTTPException(status_code=400, detail="No text could be extracted from the file")

        # Save extracted text as DOCX and PDF in Azure Blob Storage
        base_filename = file.filename.rsplit('.', 1)[0]
        #docx_filename = f"uploads/{user_id}/{contract_id}/{base_filename}.docx"
        #pdf_filename = f"uploads/{user_id}/{contract_id}/{base_filename}.pdf"
        docx_url, pdf_url = upload_contract_to_blob(file_text, "uploaded", contract_id)

        # Construct message for OpenAI
        messages = [
            {"role": "system", "content": "You are a helpful assistant analyzing uploaded files."},
            {"role": "user", "content": f"File content:\n{file_text}"}
        ]
        if prompt:
            messages.append({"role": "user", "content": prompt})

        # Call OpenAI's chat completions API
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000  # Larger limit for file processing
        )
        # Extract and return the response
        response_text = completion.choices[0].message.content
        return {
            "result": response_text,
            "docx_url": docx_url,
            "pdf_url": pdf_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")