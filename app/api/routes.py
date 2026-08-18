from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.vision_service import process_image_mock

router = APIRouter()

@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    # Validação básica de tipo
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"O arquivo {file.filename} não é uma imagem válida")

    try:
        # Ler os bytes da imagem enviada
        contents = await file.read()
        
        # Chamar o serviço de IA (neste momento, o Mock)
        img_base64 = await process_image_mock(contents)
        
        # Retorna o JSON com a imagem única processada
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "image_data": f"data:image/jpeg;base64,{img_base64}" 
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem {file.filename}: {str(e)}")