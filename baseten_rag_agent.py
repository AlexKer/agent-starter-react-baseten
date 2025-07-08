from __future__ import annotations

import os
import ssl
from pathlib import Path

import aiohttp
import certifi
from dotenv import load_dotenv
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike

from livekit import agents
from livekit.agents import Agent, AgentSession, RoomInputOptions, llm
import livekit.rtc as rtc
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

# check if storage already exists
THIS_DIR = Path(__file__).parent
PERSIST_DIR = THIS_DIR / "query-engine-storage"

# Create the embedding model
embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)

if not PERSIST_DIR.exists():
    # load the documents and create the index
    documents = SimpleDirectoryReader(THIS_DIR / "data").load_data()
    index = VectorStoreIndex.from_documents(documents, embed_model=embed_model)
    # store it for later
    index.storage_context.persist(persist_dir=str(PERSIST_DIR))
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=str(PERSIST_DIR))
    index = load_index_from_storage(storage_context, embed_model=embed_model)


@llm.function_tool
async def query_info(query: str) -> str:
    """Get more information about a specific topic"""
    
    # Set up the LLM with Baseten endpoint
    baseten_deepseek = OpenAILike(
        api_key=baseten_api_key,
        api_base="https://inference.baseten.co/v1",
        model="deepseek-ai/DeepSeek-V3-0324",
        is_chat_model=True,
    )
    
    # Use the simple query_engine pattern with custom system prompt
    query_engine = index.as_query_engine(
        use_async=True, 
        llm=baseten_deepseek,
        system_prompt="You are a helpful assistant. Answer questions based on the provided context. Respond in plain text only - no markdown, no emojis, no special formatting. Give direct, conversational answers that sound natural when spoken aloud."
    )
    res = await query_engine.aquery(query)
    print("Query result:", res)
    return str(res)

async def entrypoint(ctx: agents.JobContext):
    # Custom SSL context (you likely don't need this, something weird with my laptop)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    await ctx.connect()
    
    room = ctx.room
    
    # Wait a moment for user to join
    import asyncio
    await asyncio.sleep(2)
    
    for participant in room.remote_participants.values():
        
        # Extract ragEnabled from metadata
        if participant.metadata and '"ragEnabled":true' in participant.metadata:
            rag_enabled = True
            print(f"Found ragEnabled=true for {participant.identity}")
        elif participant.metadata in participant.metadata:
            rag_enabled = False
            print(f"Found ragEnabled=false for {participant.identity}")
        else:
            # rag_enabled = True  # default value
            print(f"No ragEnabled found, using default: {rag_enabled}")
    
    # Get ragEnabled from token metadata
    import json

    
    print(f"rag_enabled?: {rag_enabled}")
    tools = [query_info] if rag_enabled else []
    print(f"tools: {tools}")

    # Create the agent with all components directly in the constructor
    agent = Agent(
        instructions="You are a helpful voice AI assistant with access to documentation. Use the query_info tool to find relevant information when users ask questions. IMPORTANT: Since you are a voice assistant, respond in plain text only - no markdown formatting, no emojis, no code blocks, no asterisks or special characters. Use simple, conversational language that sounds natural when spoken aloud.",
        tools=tools,
        vad=silero.VAD.load(),
        stt=baseten.STT(
            api_key=baseten_api_key,
            model_endpoint="wss://model-nwx8d863.api.baseten.co/v1/websocket",  # Replace with your actual STT endpoint
        ),
        llm=openai.LLM(
            api_key=baseten_api_key, 
            base_url="https://inference.baseten.co/v1",
            model="deepseek-ai/DeepSeek-V3-0324",
        ),
        tts=baseten.TTS(
            api_key=baseten_api_key,
            model_endpoint="https://model-5qez6v2q.api.baseten.co/environments/production/predict", # Replace with your TTS endpoint
        ),
    )

    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    await session.say("Hey, how can I help you today?", allow_interruptions=True)


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))