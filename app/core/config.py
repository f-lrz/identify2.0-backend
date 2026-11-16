from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app):
    # O frontend roda em outra origem (ex.: http://localhost:5173) e o
    # navegador bloqueia a chamada à API sem esta liberação de CORS.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, substituir pelo domínio do frontend
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )