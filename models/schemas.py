from pydantic import BaseModel

class ChatRequest(BaseModel):
    prompt: str

class UploadRequest(BaseModel):
    user_id: str
    contract_id: str
    organization_id: str
    prompt: str | None = None