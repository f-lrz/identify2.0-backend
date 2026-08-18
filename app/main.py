from fastapi import FastAPI
from app.core.config import setup_cors
from app.api.routes import router as api_router

# Instancia a aplicação FastAPI com documentação Swagger configurada
app = FastAPI(
    title="IDENTIFY 2.0 Backend",
    description="API de Visão Computacional para detecção de podridão vermelha em campos de agave.",
    version="1.0.0"
)

# Aplica as configurações de CORS
setup_cors(app)

# Registra os endpoints com o prefixo /api
app.include_router(api_router, prefix="/api")

# Rota raiz de health check (para confirmar que a API está no ar)
@app.get("/")
async def root():
    return {"status": "online", "message": "Backend do IDENTIFY 2.0 ativo. Acesse /docs para testar."}