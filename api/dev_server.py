from flask import Flask, request
from spotify_stats.service import build_stats_result

app = Flask(__name__)

@app.post("/api/stats")
def stats():
    result = build_stats_result(request.data)
    return result.body, result.status

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=7071, debug=True)