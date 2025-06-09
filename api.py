from flask import Flask, request, jsonify
from db import crear_tunel, obtener_tunel_por_nombre, registrar_mensaje

app = Flask(__name__)

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
