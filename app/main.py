from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import setup_cors
from app.api.routes import router as api_router

app = FastAPI(
    title="IDENTIFY 2.0 Backend",
    description="API de Visão Computacional para detecção de podridão vermelha em campos de agave.",
    version="1.0.0"
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