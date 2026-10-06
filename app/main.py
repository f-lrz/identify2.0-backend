from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import setup_cors
from app.api.routes import router as api_router
from app.services.vision_service import USAR_MOCK, obter_detector


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Carrega o modelo ANTES de aceitar requisição. Sem isto, o primeiro
    # usuário paga ~5s extras (import do ultralytics + leitura dos pesos)
    # além dos ~11s da inferência.
    if not USAR_MOCK:
        obter_detector()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="IDENTIFY 2.0 Backend",
    # Etapa 1 de 2. O modelo atual DETECTA a presença de agave e nada mais —
    # tem uma classe só e não distingue planta doente de sadia. A classificação
    # de podridão vermelha é a etapa 2, ainda em desenvolvimento.
    description="API de Visão Computacional para detecção de plantas de agave "
                "em imagens de drone. Não realiza diagnóstico de doença.",
    version="1.1.0"
)

setup_cors(app)
app.include_router(api_router, prefix="/api")

# Serve a pasta static/
app.mount("/static", StaticFiles(directory="static"), name="static")

# Rota raiz serve a página de upload/loading/resultado
@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Health check - /health
@app.get("/health")
async def health():
    return {"status": "online", "message": "Backend do IDENTIFY 2.0 ativo."}