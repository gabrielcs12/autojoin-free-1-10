from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import asyncio
import websockets
import json
import threading

app = Flask(__name__)
CORS(app)

pets = []
connected_clients = set()

# -------------------------------
# WebSocket server
# -------------------------------
async def ws_handler(websocket, path):
    connected_clients.add(websocket)
    print("✅ Cliente conectado:", websocket.remote_address)
    try:
        async for message in websocket:
            pass
    except:
        pass
    finally:
        connected_clients.remove(websocket)
        print("❌ Cliente desconectado:", websocket.remote_address)

def start_ws_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ws_server = websockets.serve(ws_handler, "0.0.0.0", 8765)
    loop.run_until_complete(ws_server)
    print("🌐 WebSocket rodando em ws://0.0.0.0:8765")
    loop.run_forever()

def broadcast_job(job_data):
    if connected_clients:
        msg = json.dumps({
            "type": "server_update",
            "data": job_data
        })
        asyncio.run(asyncio.wait([client.send(msg) for client in connected_clients]))

# -------------------------------
# Flask endpoints
# -------------------------------
@app.route("/pets")
def get_pets():
    return jsonify(pets)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    content = data.get("content", "")
    # procura Job IDs no texto
    job_ids = re.findall(r"[0-9a-fA-F\-]{36}", content)
    if job_ids:
        for job_id in job_ids:
            new_pet = {
                "content": content,
                "job_id": job_id,
                "money": 10_000_000  # Exemplo fixo, pode ajustar
            }
            pets.append(new_pet)
            print("✅ Novo pet adicionado:", new_pet)
            # broadcast para todos clientes WebSocket
            threading.Thread(target=broadcast_job, args=(new_pet,)).start()
    return "", 204

# -------------------------------
# Start servers
# -------------------------------
if __name__ == "__main__":
    # WebSocket em thread separada
    threading.Thread(target=start_ws_server, daemon=True).start()
    # Flask
    app.run(host="0.0.0.0", port=8081)
