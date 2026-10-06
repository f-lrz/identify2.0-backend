"""Servico de visao computacional: detecta agaves na foto de drone.

ATENCAO AO ESCOPO DO MODELO. Ele detecta a PRESENCA de agave e nada mais.
Tem uma classe so ('agave') e NAO distingue planta doente de sadia. Nenhum
texto exibido ao usuario deve afirmar diagnostico com base nesta saida — ver
models/MODELO.md.

O classificador de saude (podridao vermelha) e uma etapa separada, ainda em
desenvolvimento.

Modo mock: defina AGAVE_MOCK=1 para voltar ao comportamento antigo (caixa
simulada, 3s de espera). Serve para o time de frontend trabalhar sem instalar
torch, que pesa algumas centenas de MB.
"""

from __future__ import annotations

import asyncio
import base64
import os
import threading
from pathlib import Path
from typing import Any

import cv2
import numpy as np

USAR_MOCK = os.getenv("AGAVE_MOCK", "0") == "1"
PESOS = Path(os.getenv("AGAVE_PESOS", "models/best.pt"))
DEVICE = os.getenv("AGAVE_DEVICE", "cpu")              # '0' para a primeira GPU
CONF = float(os.getenv("AGAVE_CONF", "0.30"))          # calibrado para contagem
QUALIDADE_JPEG = int(os.getenv("AGAVE_JPEG", "85"))

# Cor da caixa desenhada. AGAVE_COR aceita: preto, vermelho, magenta, ciano,
# amarelo, branco, verde. Cada caixa leva um contorno claro por tras, para nao
# sumir sobre sombra. Evite 'verde': confunde com a propria planta.
NOME_COR = os.getenv("AGAVE_COR", "vermelho")

_detector = None
_trava_carga = threading.Lock()


def obter_detector():
    """Carrega o modelo uma unica vez, na primeira requisicao.

    O import fica aqui dentro de proposito: com AGAVE_MOCK=1 o modulo nao
    precisa de torch nem ultralytics instalados.
    """
    global _detector
    if _detector is None:
        with _trava_carga:
            if _detector is None:                      # outra thread pode ter carregado
                from .agave_detector import DetectorAgave
                _detector = DetectorAgave(PESOS, device=DEVICE, conf=CONF)
    return _detector


def _codificar(img: np.ndarray) -> str:
    sucesso, buffer = cv2.imencode(".jpg", img,
                                   [cv2.IMWRITE_JPEG_QUALITY, QUALIDADE_JPEG])
    if not sucesso:
        raise ValueError("Erro ao recodificar a imagem.")
    return base64.b64encode(buffer).decode("utf-8")


def _detectar_sincrono(file_bytes: bytes) -> dict[str, Any]:
    """Roda a inferencia. BLOQUEANTE — sempre chame via asyncio.to_thread."""
    from .agave_detector import CORES, PRETO, desenhar_caixas

    det = obter_detector()
    r = det.detectar(file_bytes)
    img = desenhar_caixas(file_bytes, r["caixas"], CORES.get(NOME_COR, PRETO))
    return {
        "image_base64": _codificar(img),
        "total_agaves": r["total"],
        "largura": r["largura"],
        "altura": r["altura"],
        "conf": r["conf_usada"],
        "avisos": r["avisos"],
        "caixas": r["caixas"],
    }


async def process_image(file_bytes: bytes) -> dict[str, Any]:
    """Detecta agaves e devolve a imagem marcada em base64, mais a contagem.

    A inferencia leva ~11s em CPU e e 100% bloqueante (numpy/torch nao liberam
    o event loop). Rodar isso direto num `async def` travaria o servidor
    INTEIRO durante os 11s — inclusive o /health e as outras requisicoes. O
    `to_thread` joga o trabalho para um worker e mantem o loop livre.
    """
    if USAR_MOCK:
        return await _process_image_mock(file_bytes)
    return await asyncio.to_thread(_detectar_sincrono, file_bytes)


async def _process_image_mock(file_bytes: bytes) -> dict[str, Any]:
    """Comportamento antigo, para desenvolvimento de frontend sem o modelo."""
    await asyncio.sleep(3)

    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Erro ao decodificar a imagem.")

    altura, largura, _ = img.shape
    x1, y1 = int(largura * 0.2), int(altura * 0.2)
    x2, y2 = int(largura * 0.8), int(altura * 0.8)
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
    cv2.putText(img, "MOCK - sem modelo carregado", (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

    return {"image_base64": _codificar(img), "total_agaves": 0,
            "largura": largura, "altura": altura, "conf": 0.0,
            "avisos": ["MODO MOCK: nenhuma deteccao real foi feita."],
            "caixas": []}
