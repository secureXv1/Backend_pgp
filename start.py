import threading
from servidor_tunel import iniciar_servidor_tunel

# 👇 IMPORTAMOS LA APP DE FLASK
from api import app as flask_app

def iniciar_api():
    flask_app.run(host="0.0.0.0", port=8000)

# 🔄 Iniciar API Flask en segundo plano
api_thread = threading.Thread(target=iniciar_api, daemon=True)
api_thread.start()

# 🔌 Iniciar servidor de túneles
iniciar_servidor_tunel(puerto=5050)
