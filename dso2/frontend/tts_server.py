from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import asyncio
import edge_tts

app = Flask(__name__)
CORS(app)


async def synthesize_all(text: str, voice: str) -> bytes:
    chunks = []
    communicate = edge_tts.Communicate(text, voice)
    async for chunk in communicate.stream():
        if chunk.get("type") == "audio":
            chunks.append(chunk.get("data", b""))
    return b"".join(chunks)


@app.get("/tts")
def tts() -> Response:
    text = (request.args.get("text") or "").strip()
    voice = request.args.get("voice", "fr-FR-DeniseNeural")

    if not text:
        return jsonify({"error": "Missing query parameter: text"}), 400

    try:
        audio = asyncio.run(synthesize_all(text, voice))
        if not audio:
            return jsonify({"error": "No audio generated"}), 502
        return Response(audio, mimetype="audio/mpeg")
    except Exception as exc:
        return jsonify({"error": f"TTS synthesis failed: {exc}"}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5500, debug=False)
