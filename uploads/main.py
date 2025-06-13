from PyQt5 import QtWidgets, QtGui, QtCore
import sys
import os, json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
import base64
import threading
from chat_window import ChatWindow
from tunnel_client import TunnelClient
from password_utils import verificar_password
from db_cliente import crear_tunel, obtener_tunel_por_nombre, guardar_uuid_localmente, get_client_uuid, registrar_cliente
import platform, socket, uuid
import requests
import uuid
import socket
import platform



# 📌 Obtener datos del equipo
def obtener_info_equipo():
    return {
        "uuid": str(uuid.getnode()),
        "hostname": socket.gethostname(),
        "sistema": platform.system() + " " + platform.release()
    }

# registro de los equipos
def registrar_en_backend():
    info = obtener_info_equipo()
    try:
        response = requests.post("http://symbolsaps.ddns.net:8000/api/registrar_cliente", json=info)
        response.raise_for_status()
    except Exception as e:
        print("❌ Error al registrar cliente en el backend:", e)

# Llama esto al iniciar
registrar_en_backend()





def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()