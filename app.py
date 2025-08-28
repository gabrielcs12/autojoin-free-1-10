import asyncio
import websockets
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import os

# --------------------
# Config
# --------------------
TARGET_CHANNEL = "1401775061706346536"
MIN_MONEY = 9_000_000

# --------------------
# Flask API
# --------------------
app = Flask(__name__)
CORS(app)

pets = []

@app.route("/pets")
def get_pets():
    return jsonify(pets)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    content = data.get("content", "")
    channel_id = str(data.get("channel_id", ""))

    # Só processa se veio do canal certo
    if channel_id != TARGET_CHANNEL:
        return "", 204

    # Extrai job_ids
    job_ids = re.findall(r"[0-9a-fA-F\-]{36}", content)

    # Extrai valor tipo "9.5M/s" ou "12M/s"
    money_match = re.search(r"(\d+\.?\d*)M/s", content)
    money_val = 0
    if money_match:
        money_val = float(money_match.group(1)) * 1_000_000

    if job_ids and money_val >= MIN_MONEY:
        new_pet = {
            "content": content,
            "job_ids": job_ids,
            "money": money_val
        }
        pets.append(new_pet)
        print("✅ Novo Brainrot acima de 9M:", new_pet)

        # Envia pro WebSocket
        asyncio.run_coroutine_threadsafe(
            broadcast({
                "type": "server_update",
                "data": {
                    "money": f"{money_val/1_000_000:.1f}M/s",
                    "join_script": f'game:GetService("TeleportService"):TeleportToPlaceInstance(10998364007, "{job_ids[0]}")'
                }
            }),
            ws_loop
        )

    return "", 204

# --------------------
# WebSocket server
# --------------------
clients = set()

async def ws_handler(ws):
    print("🤝 Cliente conectado no WS")
    clients.add(ws)
    try:
        async for msg in ws:
            pass
    finally:
        clients.remove(ws)

async def broadcast(data):
    if clients:
        msg = json.dumps(data)
        await asyncio.gather(*[c.send(msg) for c in clients])

async def ws_main():
    async with websockets.serve(ws_handler, "0.0.0.0", int(os.getenv("PORT", 8765))):
        print("🌐 WebSocket rodando na porta", os.getenv("PORT", 8765))
        await asyncio.Future()

# --------------------
# Threads
# --------------------
def start_ws():
    global ws_loop
    ws_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ws_loop)
    ws_loop.run_until_complete(ws_main())

# --------------------
# Main
# --------------------
if __name__ == "__main__":
    threading.Thread(target=start_ws, daemon=True).start()
    app.run(host="0.0.0.0", port=8081)
