from typing import Union
from twilio.twiml.voice_response import VoiceResponse
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


# Add this to main.py
from fastapi import WebSocket
import base64

@app.websocket("/audio-stream")
async def audio_stream(websocket: WebSocket):
    await websocket.accept()
    print("Media stream started")

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("event") == "media":
                payload = data["media"]["payload"]
                audio_bytes = base64.b64decode(payload)
                if audio_bytes:
                    print("Received audio data")
                # Do something with audio_bytes (e.g., stream to Whisper, save, etc.)
            elif data.get("event") == "stop":
                print("Media stream ended")
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
