import socketserver
import threading
import json
from db import registrar_cliente, registrar_alias_cliente, registrar_mensaje

clientes_por_tunel = {}
lock = threading.Lock()


class TunnelHandler(socketserver.BaseRequestHandler):
    def handle(self):
        global clientes_por_tunel

        try:
            # Paso 1: recibir handshake del cliente
            datos = self.request.recv(2048).decode()
            handshake = json.loads(datos)

            tunnel_id = handshake.get("tunnel_id")
            alias = handshake.get("alias", "anónimo")
            uuid = handshake.get("uuid")
            hostname = handshake.get("hostname", "")
            sistema = handshake.get("sistema", "")

            if not tunnel_id or not alias or not uuid:
                self.request.sendall(b"ERROR: handshake incompleto\n")
                print("❌ Conexión rechazada por datos incompletos")
                return

            # Paso 2: registrar cliente y alias en la BD
            registrar_cliente(uuid, hostname, sistema)
            registrar_alias_cliente(uuid, tunnel_id, alias)

            # Paso 3: guardar la conexión
            with lock:
                if tunnel_id not in clientes_por_tunel:
                    clientes_por_tunel[tunnel_id] = []
                clientes_por_tunel[tunnel_id].append((self, alias, uuid))

            print(f"✅ [{tunnel_id}] {alias} ({uuid}) conectado")

            # Paso 4: escuchar mensajes
            while True:
                data = self.request.recv(4096)
                if not data:
                    break

                mensaje = data.decode(errors="ignore").strip()

                # Registrar en base de datos
                registrar_mensaje(tunnel_id, uuid, alias, mensaje)

                # Reenviar a otros clientes del mismo túnel
                with lock:
                    for cliente, nombre, uid in clientes_por_tunel[tunnel_id]:
                        if cliente != self:
                            try:
                                cliente.request.sendall(data)
                            except:
                                pass

        except Exception as e:
            print(f"⚠️ Error en handler: {e}")

        finally:
            with lock:
                if tunnel_id in clientes_por_tunel:
                    clientes_por_tunel[tunnel_id] = [
                        (c, a, u) for c, a, u in clientes_por_tunel[tunnel_id] if c != self
                    ]
            print(f"🛑 [{tunnel_id}] {alias} desconectado")


def iniciar_servidor_tunel(puerto=5050):
    class CustomHandler(TunnelHandler):
        pass

    with socketserver.ThreadingTCPServer(("0.0.0.0", puerto), CustomHandler) as server:
        print(f"🛰️ Servidor de túneles escuchando en puerto {puerto}")
        server.serve_forever()
