import cv2
import numpy as np
import base64
import asyncio

async def process_image_mock(file_bytes: bytes) -> str:
    # 1. Simular o tempo de processamento da IA (3 segundos) para testar o loading no front
    await asyncio.sleep(3)

    # 2. Converter os bytes recebidos para uma matriz NumPy (formato numérico que o OpenCV entende)
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Erro ao decodificar a imagem.")

    # 3. Simular a detecção: Desenhar uma caixa vermelha e um texto
    altura, largura, _ = img.shape
    x1, y1 = int(largura * 0.2), int(altura * 0.2)
    x2, y2 = int(largura * 0.8), int(altura * 0.8)

    # Cor BGR no OpenCV: (0, 0, 255) é vermelho. Espessura = 3
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)

    # Adicionar o rótulo de simulação
    texto = "Podridao Vermelha (Mock) 95%"
    cv2.putText(img, texto, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    # 4. Codificar a imagem processada de volta para JPG
    sucesso, buffer = cv2.imencode('.jpg', img)
    if not sucesso:
        raise ValueError("Erro ao recodificar a imagem.")

    # 5. Converter para Base64 para facilitar o envio e renderização no frontend
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return img_base64