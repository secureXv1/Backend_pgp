# logs_db.py
import pymysql
import time

# Conexión a la base de datos (ajusta con tus datos reales)
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='Febrero2025*-+',
    database='securex',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

def registrar_log(usuario, accion, modulo=None, ip=None):
    timestamp = int(time.time() * 1000)
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO logs (usuario, accion, modulo, fecha, ip)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (usuario, accion, modulo, timestamp, ip))
        connection.commit()
    except Exception as e:
        print(f"⚠️ Error al registrar log: {e}")
