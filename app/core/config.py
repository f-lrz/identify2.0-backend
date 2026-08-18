from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, substituir pelo domínio do frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )