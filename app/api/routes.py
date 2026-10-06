from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.vision_service import process_image

router = APIRouter()

@router.post("/analyze")
async def analyze_image(file: UploadFile = File(...)):
    # Validação básica de tipo
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"O arquivo {file.filename} não é uma imagem válida")

    try:
        # Ler os bytes da imagem enviada
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail=f"O arquivo {file.filename} está vazio")

        # Detecção de agave (NÃO é diagnóstico de doença — ver models/MODELO.md)
        resultado = await process_image(contents)

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            # mantido para não quebrar o frontend, que lê data.image_data
            "image_data": f"data:image/jpeg;base64,{resultado['image_base64']}",
            # campos novos
            "total_agaves": resultado["total_agaves"],
            "largura": resultado["largura"],
            "altura": resultado["altura"],
            "conf": resultado["conf"],
            # Se vier preenchido, MOSTRE. O caso principal é imagem
            # redimensionada, que derruba a detecção pela metade sem dar erro.
            "avisos": resultado["avisos"],
        }

    except HTTPException:
        raise
    except ValueError as e:
        # imagem corrompida / não decodificável é erro do cliente, não do servidor
        raise HTTPException(status_code=400, detail=f"Erro ao ler a imagem {file.filename}: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a imagem {file.filename}: {str(e)}")
