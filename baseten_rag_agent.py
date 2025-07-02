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

    # Read participant metadata to determine RAG state
    rag_enabled = True  # Default to True
    try:
        # Get the first participant (assuming there's only one user)
        participants = list(ctx.room.participants.values())
        if participants:
            participant = participants[0]
            if participant.metadata:
                import json
                metadata = json.loads(participant.metadata)
                rag_enabled = metadata.get('ragEnabled', True)
                print(f"RAG enabled: {rag_enabled}")
    except Exception as e:
        print(f"Error reading participant metadata: {e}")
        rag_enabled = True  # Default to True on error

    # Conditionally set tools based on RAG state
    tools = [query_info] if rag_enabled else []
    print(f"Using tools: {[tool.__name__ for tool in tools]}")

    # Create the agent with all components directly in the constructor
    agent = Agent(
        instructions="You are a helpful voice AI assistant with access to documentation. Use the query_info tool to find relevant information when users ask questions. IMPORTANT: Since you are a voice assistant, respond in plain text only - no markdown formatting, no emojis, no code blocks, no asterisks or special characters. Use simple, conversational language that sounds natural when spoken aloud.",
        tools=tools,
        vad=silero.VAD.load(),
        stt=baseten.STT(
            api_key=baseten_api_key,
            model_endpoint="wss://model-8w6kke53.api.baseten.co/v1/websocket",  # Replace with your actual STT endpoint
        ),
        llm=openai.LLM(
            api_key=baseten_api_key, 
            base_url="https://inference.baseten.co/v1",
            model="deepseek-ai/DeepSeek-V3-0324",
        ),
        tts=baseten.TTS(
            api_key=baseten_api_key,
            model_endpoint="https://model-6wg11gjw.api.baseten.co/environments/production/predict", # Replace with your TTS endpoint
        ),
    )

    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    await session.say("Hey, how can I help you today?", allow_interruptions=True)


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))