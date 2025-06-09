import mysql.connector
import os

def get_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Febrero2025*-+',
        database='securex'
    )

def crear_tunel(nombre, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tunnels (name, password_hash) VALUES (%s, %s)",
        (nombre, password_hash)
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

def registrar_cliente(uuid, hostname, sistema):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clients (uuid, hostname, sistema_operativo)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE hostname=VALUES(hostname), sistema_operativo=VALUES(sistema_operativo)
    """, (uuid, hostname, sistema))
    conn.commit()
    cursor.close()
    conn.close()

def registrar_alias_cliente(uuid, tunnel_id, alias):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO client_aliases (client_uuid, tunnel_id, alias)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE alias=VALUES(alias)
    """, (uuid, tunnel_id, alias))
    conn.commit()
    cursor.close()
    conn.close()

def registrar_mensaje(tunnel_id, uuid, alias, contenido, tipo="texto"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO tunnel_messages (tunnel_id, client_uuid, alias, contenido, tipo)
        VALUES (%s, %s, %s, %s, %s)
    """, (tunnel_id, uuid, alias, contenido, tipo))
    conn.commit()
    cursor.close()
    conn.close()
