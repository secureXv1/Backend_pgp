import threading
from servidor_tunel import iniciar_servidor_tunel

# 👇 Importa solo la app ya configurada
from api import app as flask_app

# ❌ NO registres el blueprint aquí
# from auth_api import auth_bp
# flask_app.register_blueprint(auth_bp, url_prefix="/api")

# ✅ Función para iniciar la API Flask
def iniciar_api():
    flask_app.run(host="0.0.0.0", port=8000)

# 🔄 Iniciar API Flask en hilo separado
api_thread = threading.Thread(target=iniciar_api, daemon=True)
api_thread.start()

# 🔌 Iniciar servidor de túneles (bloqueante)
iniciar_servidor_tunel(puerto=5050)

