import os
import csv
import xml.etree.ElementTree as ET
from datetime import datetime
from flask import Flask, request, jsonify
from db import crear_tunel, obtener_tunel_por_nombre, registrar_mensaje
from werkzeug.utils import secure_filename
from db import registrar_archivo
from flask import send_from_directory
from flask_cors import CORS
from io import StringIO, BytesIO
from flask import Response
from consultas_api import consultas_bp
from auth_api import auth_bp  # ← asegúrate que el archivo se llama auth_api.py
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# 🔒 Solo permite peticiones del frontend local en desarrollo
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# 💡 Cuando tengas dominio en producción, reemplaza por algo como:
# CORS(app, resources={r"/api/*": {"origins": "https://portal.securex.com"}})

# Rutas de consulta separadas
app.register_blueprint(consultas_bp)
app.register_blueprint(auth_bp)

@app.route('/api/tunnels/create', methods=['POST'])
def crear():
    try:
        data = request.json
        print("📥 Datos recibidos:", data)

        nombre = data["name"]
        clave = data["password"]
        uuid = data["uuid"]  # <- necesario para created_by

        from password_utils import hash_password
        hash_pw = hash_password(clave)

        tunnel_id = crear_tunel(nombre, hash_pw, uuid)  # <- PASAR EL uuid
        return jsonify({"tunnel_id": tunnel_id}), 201

    except Exception as e:
        print("❌ Error en /api/tunnels/create:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/api/tunnels/get', methods=['GET'])
def get_tunel():
    nombre = request.args.get("name")
    tunel = obtener_tunel_por_nombre(nombre)
    if tunel:
        return jsonify(tunel)
    else:
        return "No encontrado", 404

@app.route('/api/messages/save', methods=['POST'])
def guardar_mensaje():
    data = request.json

    tipo = data.get("tipo", "texto")
    contenido = data.get("contenido")

    if tipo == "file":
        texto_final = f"{data['alias']} envió un archivo: {contenido.get('filename', 'archivo')}"
    elif tipo == "texto":
        if isinstance(contenido, dict):
            texto_final = contenido.get("text", "")
        elif isinstance(contenido, str):
            texto_final = contenido
        else:
            texto_final = str(contenido)
    else:
        texto_final = contenido if isinstance(contenido, str) else str(contenido)

    registrar_mensaje(data["tunnel_id"], data["uuid"], data["alias"], texto_final, tipo)
    return "", 204

@app.route('/api/registrar_cliente', methods=['POST'])
def registrar_cliente():
    from db import registrar_cliente as registrar_cliente_db

    data = request.json
    uuid = data.get("uuid")
    hostname = data.get("hostname")
    sistema = data.get("sistema")

    if not uuid or not hostname or not sistema:
        return jsonify({"error": "Faltan datos"}), 400

    try:
        registrar_cliente_db(uuid, hostname, sistema)
        return jsonify({"mensaje": "Cliente registrado exitosamente"}), 200
    except Exception as e:
        print("❌ Error registrando cliente:", e)
        return jsonify({"error": "Error interno"}), 500

@app.route('/api/registrar_alias', methods=['POST'])
def registrar_alias():
    from db import registrar_alias_cliente as registrar_alias_db

    data = request.json
    uuid = data.get("uuid")
    tunnel_id = data.get("tunnel_id")
    alias = data.get("alias")

    if not uuid or not tunnel_id or not alias:
        return jsonify({"error": "Faltan datos"}), 400

    try:
        registrar_alias_db(uuid, tunnel_id, alias)
        return jsonify({"mensaje": "Alias registrado correctamente"}), 200
    except Exception as e:
        print("❌ Error registrando alias:", e)
        return jsonify({"error": "Error interno"}), 500
    
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/api/upload-file', methods=['POST'])
def upload_file():
    file = request.files.get("file")
    alias = request.form.get("alias")
    tunnel_id = request.form.get("tunnel_id")
    uuid = request.form.get("uuid")

    if not file or not alias or not tunnel_id or not uuid:
        return jsonify({"error": "Faltan datos"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    url = f"/uploads/{filename}"

    registrar_archivo(filename, url, alias, tunnel_id, uuid)
    return jsonify({"url": url, "filename": filename})

@app.route("/uploads/<path:filename>")
def descargar_archivo(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/api/tunnels/join', methods=['POST'])
def unirse_a_tunel():
    from db import obtener_tunel_por_id
    from password_utils import verificar_password

    try:
        data = request.json
        print("📥 Recibido:", data)

        tunnel_id = data.get("tunnel_id")
        password = data.get("password")
        alias = data.get("alias")

        if not tunnel_id or not password or not alias:
            print("⚠️ Faltan datos")
            return jsonify({"error": "Faltan datos"}), 400

        tunel = obtener_tunel_por_id(tunnel_id)
        print("🔍 Tunel encontrado:", tunel)

        if not tunel:
            return jsonify({"error": "Túnel no encontrado"}), 404

        if not verificar_password(password, tunel["password_hash"]):
            print("❌ Contraseña incorrecta")
            return jsonify({"error": "Contraseña incorrecta"}), 401

        print("✅ Validación exitosa")
        return jsonify({"mensaje": "Acceso permitido"}), 200
    
    except Exception as e:
        print("❌ Error interno:", e)
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)