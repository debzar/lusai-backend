from fastapi import APIRouter, UploadFile, File, HTTPException, status
from services.supabase_upload import upload_file_to_supabase

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/rtf": ".rtf",
    "text/rtf": ".rtf"
}

@router.post("/upload-file", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tipo de archivo no permitido. Solo PDF, DOC, DOCX o RTF.")
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo está vacío.")
    try:
        public_url = upload_file_to_supabase(file_bytes, file.filename, file.content_type)
        return {"url": public_url, "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir el archivo: {str(e)}")
