from typing import Dict
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Start, Stream
from twilio.rest import Client
from fastapi import FastAPI
from fastapi import WebSocket
from google import genai
from google.genai import types
from pydub import AudioSegment
import base64
import numpy as np
import os

app = FastAPI()
ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]

client = Client(ACCOUNT_SID, AUTH_TOKEN)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/voice")
async def voice():
    response = VoiceResponse()

    # Start streaming audio to your WebSocket server
    start = Start()
    start.stream(
        url="wss://sample-voice-agent.onrender.com/audio-stream",
        status_callback="https://sample-voice-agent.onrender.com/stream_callback"
    )
    
    response.append(start)
    response.say("Welcome to the AI-powered voice agent. How can I assist you today?")
    return Response(content=str(response), media_type="application/xml")

@app.post("/stream_callback")
def callback_streaming(data: Dict):
    print(data)
    return {"received": data}

@app.websocket("/audio-stream")
async def audio_stream(websocket: WebSocket):
    
    await websocket.accept()
    stream_sid = None
    audio_buffer = bytearray()
    
    greeting_text = "Hello! How can I help you?"
    # greeting_audio_mulaw_b64 = await text_to_speech_and_encode(greeting_text)
    # await websocket.send_json({ "event": "media", "streamSid": stream_sid, "media": { "payload": greeting_audio_mulaw_b64 }})
    print("Media stream started")

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("event") == "media":
                payload = data["media"]["payload"]
                audio_mulaw_bytes = base64.b64decode(payload)

                # 1. Create an AudioSegment from the raw mulaw data
                audio_segment = AudioSegment(
                    data=audio_mulaw_bytes,
                    sample_width=1,  # mulaw is 8-bit, so 1 byte
                    frame_rate=8000,
                    channels=1
                )

                # 2. Resample to 16kHz for the AI model
                resampled_segment = audio_segment.set_frame_rate(16000)

                # 3. Get the raw PCM bytes
                audio_pcm_bytes = resampled_segment.raw_data
                if audio_pcm_bytes:
                    print("Received audio data")
                    
                    audio_blob = types.Blob(
                        data=audio_pcm_bytes, 
                        mime_type="audio/pcm;rate=16000"
                    )
                    response = await get_genai_response(audio_blob)
                    resp.say(response)

            
            elif data.get("event") == "stop":
                print("Media stream ended")
                break
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
        

async def get_genai_response(audio_blob: types.Blob):
    client = genai.Client(
        api_key=os.environ.get("GENAI_API_KEY")
    )
    
    model = "gemini-2.0-flash-live-001"

    config = types.LiveConnectConfig(response_modalities=["AUDIO"])


    async with client.aio.live.connect(model=model, config=config) as session:
        
        await session.send_realtime_input(
                audio=audio_blob
            )
        
        response = []
    
        async for message in session.receive():
            if message.text:
                response.append(message.text)
    
        print("".join(response))
        return "".join(response)