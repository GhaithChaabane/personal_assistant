
import asyncio
import base64
import json
import wave
import struct
from websockets.asyncio.client import connect
from google import genai
import pyaudio
from playsound3 import playsound
from concurrent.futures import CancelledError
import logging
import os
from dotenv import load_dotenv
from google.genai.types import GoogleSearch,Tool , Content, Part
import traceback


google_search_tool = Tool(google_search=GoogleSearch())

load_dotenv()

# Configure logging
logging.basicConfig(filename='gemini_app.log',level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = genai.Client(
    api_key=os.environ.get("API_KEY"),
    http_options={"api_version": "v1beta"},
)
CONFIG = genai.types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=genai.types.SpeechConfig(
        voice_config=genai.types.VoiceConfig(
            prebuilt_voice_config=genai.types.PrebuiltVoiceConfig(voice_name = "Zephyr")
        )
    ),
    tools=[google_search_tool],
    system_instruction=Content(
         parts=[Part.from_text(text="""You are a helpful assistant.""")],
         role="user",
    )
)
# todo add logging and thinking 
# todo start frontend

class gemini_audio:
    """
    Docstring for gemini_audio
    """
    def __init__(self,cleanup_event=None,on_connect=None):
            
        # ----- CONFIG -----
        self.API_KEY = os.environ.get("API_KEY")
        self.MODEL_ID = "gemini-2.5-flash-native-audio-preview-12-2025"
        self.WS_URI = (
            "wss://generativelanguage.googleapis.com/ws/"
            "google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent"
            f"?key={self.API_KEY}"
        )

        # 100 ms chunk at 16kHz, 16-bit mono: 16000 * 0.1 * 2 bytes = 3200 bytes
        self.CHUNK_MS = 100
        self.FORMAT = pyaudio.paInt16 
        self.CHANNELS = 1  
        self.CHUNK = 512 
        self.RATE = 16000 
        self.RECEIVE_SAMPLE_RATE = 24000
        self.output_user="reply.wav"
        self.user_input="question.wav"
        self.audio_queue=asyncio.Queue()
        self.ws = None
        self.on_connect = on_connect
        self.audio_output=asyncio.Queue()
        self.running = True
        self.cleanup_event = cleanup_event
        self.allow_interruptions = False
        # When True the model is currently sending audio; used to pause sending mic chunks
        self.is_model_speaking = False




    async def capture_audio(self):
        """Capture audio from your Mac's microphone and send to Gemini in realtime."""
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )

            while True:
                try:
                    data = await asyncio.to_thread(stream.read, self.CHUNK, exception_on_overflow=False)                    
                    realtime_input_msg = {
                    "data": data,
                    "mime_type": "audio/pcm"
                    }
                    # If the model is speaking and we don't allow interruptions,
                    # skip sending microphone chunks to avoid overlap/crackle.
                    if self.is_model_speaking and not self.allow_interruptions:
                        await asyncio.sleep(0.01)
                        continue
                    await self.audio_queue.put(realtime_input_msg)
                except OSError as e:
                    print(f"Audio capture error: {e}")
                    await asyncio.sleep(0.1)  # Add small delay before retrying
                    continue

        except CancelledError:
            print("Audio capture cancelled")
        except Exception as e:
            print(f"Unexpected error in capture_audio: {e}")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    async def send_data(self):
            while True:
                data=await self.audio_queue.get()
                # await self.ws.send(json.dumps(data))
                await self.ws.send_realtime_input(audio=data)


    async def receive_server_messages(self):

        """Read from the websocket and write PCM chunks to the output queue."""
        try:
            while True:
                turn = self.ws.receive()
                async for response in turn:
                    if data := response.data:
                        self.is_model_speaking = True
                        self.audio_output.put_nowait(data)
                        continue
                    if text := response.text:
                        print(text, end="")
                    if response.server_content and getattr(response.server_content, "turn_complete", False):
                            self.is_model_speaking = False
                            while not self.audio_queue.empty():
                                self.audio_queue.get_nowait()
                # If you interrupt the model, it sends a turn_complete.
                # For interruptions to work, we need to stop playback.
                # So empty out the audio queue because it may have loaded
                # much more audio than has played yet.
                while not self.audio_queue.empty():
                    self.audio_queue.get_nowait()
        except asyncio.CancelledError:
            pass


    async def play_responses(self):
            """Pull audio data from the queue and play it through speakers."""
            audio = pyaudio.PyAudio()
            stream = audio.open(
                    format=self.FORMAT,
                    channels=self.CHANNELS,
                    rate=self.RECEIVE_SAMPLE_RATE,
                    output=True
            )

            try:
                while True:
                    audio_chunk = await self.audio_output.get()
                    await asyncio.to_thread(stream.write, audio_chunk)
            
            except CancelledError:
                   print("Playback cancelled")
            except Exception as e:
                   
                   print(f"[play_responses] {type(e).__name__}: {e}")

                   print(f"Unexpected error in play_responses: {e}")
            finally:
                    stream.stop_stream()
                    stream.close()
                    audio.terminate()


    async def main(self):
        """main func"""
        logger.info("Attempting to connect to Gemini at {self.WS_URI}")
        try:
            print(f"Connecting to: {self.MODEL_ID}")
            # self.ws=await connect(self.WS_URI,additional_headers={"Content-Type": "application/json"})
            async with (
                client.aio.live.connect(model=self.MODEL_ID, config=CONFIG) as session,
                asyncio.TaskGroup() as tg,
            ):
                logger.info(" WebSocket connection established.")
                self.ws = session
                # 3) Setup (camelCase)
                logger.info(" Sending setup message.")
                        
                logger.info(" Waiting for setup response.")
                # await self.ws.send(json.dumps(setup_msg))
                # connect() already waited for setup; session.session_id is set when setup succeeded
                if getattr(session, "session_id", None):
                    print("Setup Accepted!")
                
                
                tg.create_task(self.capture_audio())
                tg.create_task(self.send_data())
                tg.create_task(self.receive_server_messages())
                tg.create_task(self.play_responses())


        except Exception as e:
            logger.exception("Error in Gemini connection")
            print("Error in Gemini connection: ", end="")
            # Print the full exception (including ExceptionGroup sub-exceptions)
            traceback.print_exception(type(e), e, e.__traceback__, chain=True)
#TODO add google search tool
if __name__ == "__main__":

    gemini=gemini_audio()
    asyncio.run(gemini.main())
