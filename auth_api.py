from flask import Blueprint, request, jsonify
from db import get_connection
from password_utils import hash_password, verificar_password
from logs_db import registrar_log
from flask import request

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/api/auth/register", methods=["POST"])
def registrar_usuario():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    rol = data.get("rol")

    if not username or not password or rol not in ["admin", "consulta"]:
        return jsonify({"success": False, "error": "Datos inválidos"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"success": False, "error": "Usuario ya existe"}), 409

        hashed = hash_password(password)
        cursor.execute(
            "INSERT INTO usuarios (username, password, rol) VALUES (%s, %s, %s)",
            (username, hashed, rol)
        )
        conn.commit()
        return jsonify({"success": True, "message": "Usuario creado exitosamente"}), 201
    except Exception as e:
        print("❌ Error registrando usuario:", e)
        return jsonify({"success": False, "error": "Error interno del servidor"}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, password, rol, activo FROM usuarios WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and verificar_password(password, user["password"]):
            if user["activo"] != 1:
                return jsonify({"success": False, "error": "Usuario inactivo"}), 403

            # ✅ REGISTRO DEL LOG
            ip = request.remote_addr
            registrar_log(username, "Inicio de sesión exitoso", "Autenticación", ip)

            return jsonify({
                "success": True,
                "id": user["id"],
                "username": username,
                "rol": user["rol"]
            }), 200

        else:
            return jsonify({"success": False, "error": "Credenciales incorrectas"}), 401

    except Exception as e:
        print("❌ Error en login:", e)
        return jsonify({"success": False, "error": "Error interno"}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route("/api/auth/change-password", methods=["POST"])
def cambiar_password():
    data = request.json
    username = data.get("username")
    anterior = data.get("anterior")
    nueva = data.get("nueva")

    if not username or not anterior or not nueva:
        return jsonify({"success": False, "error": "Datos incompletos"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password FROM usuarios WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user or not verificar_password(anterior, user["password"]):
            return jsonify({"success": False, "error": "Contraseña anterior incorrecta"}), 401

        hashed = hash_password(nueva)
        cursor.execute("UPDATE usuarios SET password = %s WHERE username = %s", (hashed, username))
        conn.commit()

        # ✅ REGISTRAR LOG
        from logs_db import registrar_log
        ip = request.remote_addr
        registrar_log(username, "Cambio de contraseña exitoso", "Autenticación", ip)

        return jsonify({"success": True, "message": "Contraseña actualizada exitosamente"}), 200

    except Exception as e:
        print("❌ Error cambiando contraseña:", e)
        return jsonify({"success": False, "error": "Error interno"}), 500
    finally:
        cursor.close()
        conn.close()



@auth_bp.route("/api/usuarios", methods=["GET"])
def listar_usuarios_registrados():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, rol, creado_en, activo FROM usuarios ORDER BY id DESC")
        usuarios = cursor.fetchall()
        return jsonify(usuarios)
    except Exception as e:
        print("❌ Error listando usuarios registrados:", e)
        return jsonify({"error": "Error interno"}), 500
    finally:
        cursor.close()
        conn.close()




@auth_bp.route("/api/usuarios/<int:user_id>/activar", methods=["POST"])
def activar_usuario(user_id):
    data = request.json
    activo = data.get('activo')

    try:
        # ⚠️ Forzar conversión a 0 o 1
        activo_valor = 1 if str(activo).lower() == "true" or activo is True else 0

        conn = get_connection()
        cursor = conn.cursor()

        # Obtener username para el log (opcional pero útil)
        cursor.execute("SELECT username FROM usuarios WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        username = result[0] if result else f"usuario_id:{user_id}"

        cursor.execute("UPDATE usuarios SET activo = %s WHERE id = %s", (activo_valor, user_id))
        conn.commit()

        # ✅ REGISTRAR LOG
        from logs_db import registrar_log
        ip = request.remote_addr
        estado = "Activado" if activo_valor == 1 else "Desactivado"
        registrar_log(username, f"Usuario {estado}", "Gestión de usuarios", ip)

        return jsonify({'success': True, 'activo': bool(activo_valor)})
    except Exception as e:
        print("❌ Error actualizando usuario:", e)
        return jsonify({'success': False, 'error': 'Error interno'}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route("/api/usuarios/<int:user_id>/cambiar-rol", methods=["POST"])
def cambiar_rol_usuario(user_id):
    data = request.json
    nuevo_rol = data.get("rol")

    if nuevo_rol not in ["admin", "consulta"]:
        return jsonify({"success": False, "error": "Rol no válido"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Obtener username para registrar en el log
        cursor.execute("SELECT username FROM usuarios WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        username = result[0] if result else f"usuario_id:{user_id}"

        cursor.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol, user_id))
        conn.commit()

        # ✅ REGISTRO DEL LOG
        from logs_db import registrar_log
        ip = request.remote_addr
        registrar_log(username, f"Rol cambiado a {nuevo_rol}", "Gestión de usuarios", ip)

        return jsonify({"success": True, "message": "Rol actualizado correctamente"})
    except Exception as e:
        print("❌ Error cambiando rol:", e)
        return jsonify({"success": False, "error": "Error interno"}), 500
    finally:
        cursor.close()
        conn.close()


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    data = request.json
    username = data.get("username")  # Se espera que el frontend lo envíe
    ip = request.remote_addr

    if not username:
        return jsonify({"success": False, "error": "Falta el nombre de usuario"}), 400

    try:
        registrar_log(username, "Cierre de sesión", "Autenticación", ip)
        return jsonify({"success": True, "message": "Sesión cerrada correctamente"}), 200
    except Exception as e:
        print("❌ Error en logout:", e)
        return jsonify({"success": False, "error": "Error interno"}), 500









