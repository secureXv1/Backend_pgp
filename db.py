import mysql.connector
import os
import time 

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Febrero2025*-+',
        database='securex'
    )



def crear_tunel(nombre, password_hash, created_by):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp_ms = int(time.time() * 1000)  # milisegundos

    cursor.execute(
        "INSERT INTO tunnels (name, password_hash, created_by, created_at) VALUES (%s, %s, %s, %s)",
        (nombre, password_hash, created_by, timestamp_ms)
    )
    conn.commit()
    tunnel_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return tunnel_id

def obtener_tunel_por_nombre(nombre):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tunnels WHERE name = %s", (nombre,))
    tunel = cursor.fetchone()
    cursor.close()
    conn.close()
    return tunel

def obtener_tunel_por_id(tunnel_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM tunnels WHERE id = %s", (tunnel_id,))
    tunel = cursor.fetchone()
    cursor.close()
    conn.close()
    return tunel

def registrar_cliente(uuid, hostname, sistema):
    conn = get_connection()
    cursor = conn.cursor()
    timestamp_ms = int(time.time() * 1000)

    cursor.execute("""
        INSERT INTO clients (uuid, hostname, sistema_operativo, creado_en)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            hostname=VALUES(hostname), 
            sistema_operativo=VALUES(sistema_operativo)
    """, (uuid, hostname, sistema, timestamp_ms))

    conn.commit()
    cursor.close()
    conn.close()

def registrar_alias_cliente(uuid, tunnel_id, alias):
    import time
    conn = get_connection()
    cursor = conn.cursor()
    timestamp_ms = int(time.time() * 1000)

    # Verificar si ya existe ese registro exacto
    cursor.execute("""
        SELECT id FROM client_aliases
        WHERE client_uuid = %s AND tunnel_id = %s AND alias = %s
    """, (uuid, tunnel_id, alias))
    
    existe = cursor.fetchone()

    if existe:
        # Solo actualizar timestamp
        cursor.execute("""
            UPDATE client_aliases
            SET conectado_en = %s
            WHERE client_uuid = %s AND tunnel_id = %s AND alias = %s
        """, (timestamp_ms, uuid, tunnel_id, alias))
    else:
        # Insertar nuevo registro
        cursor.execute("""
            INSERT INTO client_aliases (client_uuid, tunnel_id, alias, conectado_en)
            VALUES (%s, %s, %s, %s)
        """, (uuid, tunnel_id, alias, timestamp_ms))

    conn.commit()
    cursor.close()
    conn.close()

def registrar_mensaje(tunnel_id, client_uuid, alias, contenido, tipo="texto"):
    import time
    conn = get_connection()
    cursor = conn.cursor()

    enviado_en = int(time.time() * 1000)  # milisegundos

    cursor.execute("""
        INSERT INTO tunnel_messages (tunnel_id, client_uuid, alias, contenido, tipo, enviado_en)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (tunnel_id, client_uuid, alias, contenido, tipo, enviado_en))

    conn.commit()
    cursor.close()
    conn.close()

def registrar_archivo(filename, url, sender_alias, tunnel_id, uuid):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tunnel_files (filename, url, sender_alias, tunnel_id, client_uuid)
        VALUES (%s, %s, %s, %s, %s)
    """, (filename, url, sender_alias, tunnel_id, uuid))
    conn.commit()
    cursor.close()
    conn.close()