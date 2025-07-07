<img src="./.github/assets/app-icon.png" alt="Voice Assistant App Icon" width="100" height="100">

# Voice Agent with RAG

Realtime voice agent with RAG powered by Baseten inference, Livekit orchestration, and LlamaIndex RAG.

This is a voice assistant built with [LiveKit Agents](https://docs.livekit.io/agents) that provides a [RAG](https://aws.amazon.com/what-is/retrieval-augmented-generation/) interface using [Baseten](https://baseten.co) inference endpoints. It supports voice interactions with access to custom documentation through vector search.

This application uses Baseten's DeepSeek models API for LLM, dedicated STT/TTS endpoints, and a local vector database for document retrieval. 

![App screenshot](/.github/assets/frontend-screenshot.jpeg)

## Prerequisites

Before getting started, you'll need:

1. **Baseten Account**: Sign up at [baseten.co](https://baseten.co) and get your API key
2. **LiveKit Account**: Sign up at [cloud.livekit.io](https://cloud.livekit.io) and get your API key, API secret, and LiveKit URL
3. **Python 3.10+**: Ensure you have Python installed on your system. We suggest using the [pyenv](https://github.com/pyenv/pyenv) library and starting in a fresh environment.

## Quick Start

### Step 1: Deploy Models on Baseten

Create deployments of these models from the Baseten model library:
- **Orpheus-3b** Dedicated (TTS)
- **Whisper Large v3 Streaming** Dedicated (STT)
- **DeepSeekV3** Models API (LLM)

### Step 2: Set Up Repository and Install Dependencies

```bash
git clone https://github.com/basetenlabs/voice-agent-baseten.git
cd voice-agent-baseten
pip install -r requirements.txt
pnpm install
```

### Step 3: Configure Environment

Create `.env.local` with your API keys (see `.env.example`):

```bash
# LiveKit credentials
LIVEKIT_API_KEY=<your_livekit_api_key>
LIVEKIT_API_SECRET=<your_livekit_api_secret>
LIVEKIT_URL=<your_livekit_url>

# Baseten credentials
BASETEN_API_KEY=<your_baseten_api_key>
```

### Step 4: Update Endpoints

Replace the endpoints in `baseten_rag_agent.py`:
- **Line 114**: Your actual Whisper WebSocket endpoint
- **Line 123**: Your actual Orpheus HTTPS endpoint

### Step 5: Add Your Docs for RAG
This step is optional as we've prefillde the data folder with raw_data.txt.

Option A: Scrape live docs
```bash
# Edit scrape_docs.py with your BASE_URL
python scrape_docs.py
```

Option B: Manually add `.txt` files to the `data/` folder

### Step 6: Run the Application

Open two terminal sessions:

```bash
# Terminal 1: Start the web app
pnpm dev

# Terminal 2: Start the voice agent
python baseten_rag_agent.py dev
```

Visit http://localhost:3000 and click 'Smart Demo' or 'Fast Demo' to start chatting!

## How It Works

We use 3 core libraries:

- **LiveKit Agents**: Orchestration framework for multimodal and voice AI
- **Baseten**: AI inference platform for production-grade open-source models
- **LlamaIndex**: Orchestration framework for robust RAG over complex documents

The voice agent creates a complete pipeline: **STT → LLM → TTS** with RAG capabilities through the `query_info` tool that retrieves relevant context from your documentation.

## Credits

Thank you to our friends at LiveKit for supporting our integration. You can find a number of LiveKit voice agents examples in their recipes page which can be adapted to use open source models deployed on Baseten, including the agent starter kit which we adapted for this demo.