import os
from flask import Flask, request, jsonify
from db import crear_tunel, obtener_tunel_por_nombre, registrar_mensaje
from werkzeug.utils import secure_filename
from db import registrar_archivo
from flask import send_from_directory
from flask_cors import CORS


app = Flask(__name__)

# 🔒 Solo permite peticiones del frontend local en desarrollo
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# 💡 Cuando tengas dominio en producción, reemplaza por algo como:
# CORS(app, resources={r"/api/*": {"origins": "https://portal.securex.com"}})


@app.route('/api/tunnels/create', methods=['POST'])
def crear():
    try:
        data = request.json
        print("📥 Datos recibidos:", data)

        nombre = data["name"]
        clave = data["password"]

        from password_utils import hash_password
        hash_pw = hash_password(clave)

        tunnel_id = crear_tunel(nombre, hash_pw)
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
    registrar_mensaje(data["tunnel_id"], data["uuid"], data["alias"], data["contenido"], data.get("tipo", "texto"))
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

@app.route("/api/tunnels", methods=["GET"])
def listar_tuneles():
    from db import get_connection
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, name, created_at 
            FROM tunnels 
            ORDER BY id DESC
        """)
        tuneles = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(tuneles)
    except Exception as e:
        print("❌ Error listando túneles:", e)
        return jsonify({"error": "Error interno"}), 500

    
@app.route("/api/messages", methods=["GET"])
def listar_mensajes():
    from db import get_connection
    tunnel_id = request.args.get("tunnel_id")

    if not tunnel_id:
        return jsonify({"error": "Falta el parámetro tunnel_id"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, client_uuid, alias, contenido, tipo
            FROM tunnel_messages
            WHERE tunnel_id = %s
            ORDER BY id DESC
            LIMIT 100
        """, (tunnel_id,))
        mensajes = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(mensajes)
    except Exception as e:
        print("❌ Error listando mensajes:", e)
        return jsonify({"error": "Error interno"}), 500
    
@app.route("/api/files", methods=["GET"])
def listar_archivos():
    from db import get_connection
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, filename FROM tunnel_files ORDER BY id DESC")
        archivos = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(archivos)
    except Exception as e:
        print("❌ Error listando archivos:", e)
        return jsonify({"error": "Error interno"}), 500

@app.route("/api/users", methods=["GET"])
def listar_usuarios():
    from db import get_connection
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT DISTINCT client_uuid AS uuid, alias
            FROM client_aliases
            ORDER BY alias
        """)
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(usuarios)
    except Exception as e:
        print("❌ Error listando usuarios:", e)
        return jsonify({"error": "Error interno"}), 500
    
    
@app.route("/api/files_by_day", methods=["GET"])
def archivos_por_dia():
    from db import get_connection
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DATE(uploaded_at) as fecha, COUNT(*) as total
            FROM tunnel_files
            GROUP BY DATE(uploaded_at)
            ORDER BY fecha
        """)
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify([
            {"fecha": str(row[0]), "total": row[1]}
            for row in resultados
        ])
    except Exception as e:
        print("❌ Error agrupando archivos:", e)
        return jsonify({"error": "Error interno"}), 500

@app.route("/api/clientes", methods=["GET"])
def listar_clientes():
    from db import get_connection
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT uuid, hostname, sistema_operativo, creado_en
            FROM clients
            ORDER BY creado_en DESC
        """)
        clientes = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(clientes)
    except Exception as e:
        print("❌ Error listando clientes:", e)
        return jsonify({"error": "Error interno"}), 500
    
@app.route("/api/tunnels/<int:tunnel_id>/participantes", methods=["GET"])
def listar_participantes(tunnel_id):
    from db import get_connection
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT DISTINCT ca.client_uuid, ca.alias, MAX(ca.conectado_en) AS conectado_en, cl.hostname
            FROM client_aliases ca
            LEFT JOIN clients cl ON cl.uuid = ca.client_uuid
            WHERE ca.tunnel_id = %s
            GROUP BY ca.client_uuid, ca.alias, cl.hostname
            ORDER BY conectado_en DESC
        """, (tunnel_id,))
        
        participantes = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(participantes)
    except Exception as e:
        print("❌ Error listando participantes:", e)
        return jsonify({"error": "Error interno"}), 500










  

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)



