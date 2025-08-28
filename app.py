from flask import Flask, request, jsonify
from flask_cors import CORS
import re

app = Flask(__name__)
CORS(app)

jobs = []

@app.route("/jobs")
def get_jobs():
    return jsonify(jobs)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    content = data.get("content", "")
    job_ids = re.findall(r"[0-9a-fA-F\-]{36}", content)
    if job_ids:
        for job_id in job_ids:
            job_entry = {
                "job_id": job_id,
                "money": 10_000_000  # Exemplo fixo acima de 9M
            }
            jobs.append(job_entry)
            print("✅ Novo Job recebido:", job_entry)
    return "", 204

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
