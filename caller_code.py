from __future__ import annotations

import os
import ssl

import aiohttp
import certifi
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions
from livekit.plugins import (
    openai,
    noise_cancellation,
    silero,
    baseten,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Load environment variables
load_dotenv()
baseten_api_key = os.getenv("BASETEN_API_KEY")
if not baseten_api_key:
    raise ValueError("BASETEN_API_KEY environment variable is required")


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")


async def entrypoint(ctx: agents.JobContext):
    # Custom SSL context (you likely don't need this, something weird with my laptop)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    await ctx.connect()

    session = AgentSession(
        stt=baseten.STT(
            api_key=baseten_api_key,
            model_endpoint="wss://model-4w5ljj7q.api.baseten.co/v1/websocket",  # Replace with your actual STT endpoint
        ),
        llm=openai.LLM(
            api_key=baseten_api_key,
            base_url="https://inference.baseten.co/v1",
            model="deepseek-ai/DeepSeek-V3-0324",
        ),
        tts=baseten.TTS(
            api_key=baseten_api_key,
            model_endpoint="https://model-5qez6v2q.api.baseten.co/environments/production/predict",  # Replace with your TTS endpoint
        ),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))