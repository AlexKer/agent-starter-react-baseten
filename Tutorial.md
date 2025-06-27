<img src="./.github/assets/app-icon.png" alt="Voice Assistant App Icon" width="100" height="100">

# How to build a Voice Agent with RAG, a.k.a your Jarvis, with Livekit, Baseten, and LlamaIndex

Voice is a much more natural intuitive interface than typing in a chatbox for most of us. Current closed source offerings leaves a lot to be desired for real-time voice AI application builders in both cost, latency, and control (fine-tuning). But with the advent of opensource speech-to-text, LLMs, text-to-speech models, building personal voice agents is possible for anyone to build.

![App screenshot](/.github/assets/frontend-screenshot.jpeg)[To be replaced with the latest frontend interface, maybe gif?]

Whether you want to create your own Jarvis, create hallucination-reduced customer support voice agents, or help your employees navigate company knowledge by giving them a seasoned mentor with corporate context, this tutorial is an entry-point to help you do that.

We use 3 core libraries in building this project. 
1. [LiveKit Agents](https://docs.livekit.io/agents), which is an orchestration framework for production-grade multimodal and voice AI, including thoughtful features like turn detection, noise cancellation and interruption handling. 
2.  [Baseten](https://baseten.co), AI inference platform that allows you run production grade open-source models on.
3. [LlamaIndex](https://www.llamaindex.ai), AI orchestration framework that allows you build robust RAG over complex documents and agentic workflows in enterprise. 

## Prerequisites

Before getting started, you'll need:

1. **Baseten Account**: Sign up at [baseten.co](https://baseten.co) and get your API key. You would need 2 dedicated employment endpoints (STT, TTS) and a deepseek models api endpoint.
2. **LiveKit Account**: Sign up at [cloud.livekit.io](https://cloud.livekit.io) and get your API key, API secret, and Livekit URL.
3. **Python 3.8+**: Ensure you have Python installed on your system

## Quick start guide (If you just want to use it right away!)

1. Clone the repository
2. `pip install -r requirements.txt`
3. Replace the 4 endpoints in `baseten_rag_agent.py` with the appropriate endpoints from your Baseten account. You can use the same LLM for both RAG and part of the STT,LLM,TTS pipeline. The example uses Deepseek for both.
4. Set api keys, see .env.example and create your own .env.local.
5. Open scrape_docs and replace `BASE_URL` with your own docs that you want to perform RAG on. Then run `python scrape_docs.py` to scrape a set of live docs based on a sitemap. Alternatively, manaually fill the `data` folder with txt files.
6. `pnpm dev` to launch the next js webapp, and visit http://localhost:3000 on your browser.
7. `python baseten_rag.py dev` to connect the voice agent to livekit cloud room
7. Click join call in the web app to join the same livekit cloud room as the voice agent.
8. Start chatting in real-time!

### Pipeline

The core of our voice agent is the `entrypoint` function that orchestrates the entire pipeline. Let's break down how it connects to LiveKit and strings together the three AI models.

The `entrypoint` function serves as the main orchestrator that:

1. **Establishes Connection**: First connects to LiveKit using `ctx.connect()` with custom SSL configuration for secure communication
2. **Creates the Agent**: Instantiates an `Agent` with all the necessary components:
   - **Instructions**: Defines the agent's personality and behavior, emphasizing plain text responses suitable for voice interaction
   - **Tools**: Includes the `query_info` function for RAG capabilities
   - **VAD (Voice Activity Detection)**: Uses Silero VAD to detect when users are speaking
   - **STT (Speech-to-Text)**: Baseten's WhisperV3 model converts speech to text via WebSocket
   - **LLM (Language Model)**: DeepSeekV3 handles reasoning and response generation
   - **TTS (Text-to-Speech)**: Orpheus3B converts the AI's text responses back to speech
3. **Manages Session**: Creates an `AgentSession` and starts it with the agent and room context
4. **Initiates Interaction**: Sends an initial greeting to begin the conversation

This creates a complete voice AI pipeline where audio flows from the user through STT → LLM → TTS back to the user, with RAG capabilities available through the `query_info` tool, which we will now get into!

---[insert graphic/visual on the entire pipeline]---

```
async def entrypoint(ctx: agents.JobContext):
    # Custom SSL context (you likely don't need this, something weird with my laptop)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    await ctx.connect()

    # Create the agent with all components directly in the constructor
    agent = Agent(
        instructions="You are a helpful voice AI assistant with access to documentation. Use the query_info tool to find relevant information when users ask questions. IMPORTANT: Since you are a voice assistant, respond in plain text only - no markdown formatting, no emojis, no code blocks, no asterisks or special characters. Use simple, conversational language that sounds natural when spoken aloud.",
        tools=[query_info],
        vad=silero.VAD.load(),
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
    )

    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)

    await session.say("Hey, how can I help you today?", allow_interruptions=True)
```



## RAG (Retrieval Augmented Generation)
To reduce hallcuination, we want to perform RAG. RAG is a technique ground the LLM responses by supplying it with relevant information from a source of truth along with user query. Keeping the latency down, we can use the HuggingFace `BAAI/bge-small-en-v1.5`, a lightweight embedding. We then write the following vector index from documents in the data folder if it doesn't exist, or loads an existing index from storage to enable efficient semantic search and retrieval. We assume that you've loaded documents in a .txt format into a data folder on the same directory level.


```
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
```

Now, how do we actually perform RAG? The decorator within Livekit transforms a regular Python function into a tool that the voice agent can call when needed. Here, we can query more info by retrieve relevant context from our previously built vector index and have our Deepseek endpoint synthesize and respond.

```
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
```

Credits: this project is adapted from Recipes from Livekit, specifically, https://github.com/livekit-examples/agent-starter-react.