from typing import Union
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Start, Stream
from fastapi import FastAPI
from fastapi import WebSocket
import base64

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/voice")
async def voice():
    response = VoiceResponse()

    # Start streaming audio to your WebSocket server
    start = Start()
    start.stream(url="wss://sample-voice-agent.onrender.com/audio-stream")
    response.append(start)

    response.say("You are now connected to the assistant.")
    response.pause(length=30)  # Keep the call open
    return Response(content=str(response), media_type="application/xml")

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
