<img src="./.github/assets/app-icon.png" alt="Voice Assistant App Icon" width="100" height="100">

# Voice Agent with RAG

Voice agent, with the full context of your business, responding in real-time. Powered by Baseten inference, Livekit orchestration, and LlamaIndex RAG.

This is a voice assistant built with [LiveKit Agents](https://docs.livekit.io/agents) that provides a [RAG](https://aws.amazon.com/what-is/retrieval-augmented-generation/) interface using [Baseten](https://baseten.co) inference endpoints. It supports voice interactions with access to custom documentation through vector search. 

This application uses Baseten's DeepSeek models API for LLM, dedicated STT/TTS endpoints, and a local vector database for document retrieval. 

![App screenshot](/.github/assets/frontend-screenshot.jpeg)

## Prerequisites

Before getting started, you'll need:

1. **Baseten Account**: Sign up at [baseten.co](https://baseten.co) and get your API key. You would need 2 dedicated employment endpoints (STT, TTS) and a deepseek models api endpoint.
2. **LiveKit Account**: Sign up at [cloud.livekit.io](https://cloud.livekit.io) and get your API key, API secret, and Livekit URL.
3. **Python 3.8+**: Ensure you have Python installed on your system

## Getting started

1. Clone the repository
2. `pip install -r requirements.txt`
3. Replace the 4 endpoints in `baseten_rag_agent.py` with the appropriate endpoints from your Baseten account. You can use the same LLM for both RAG and part of the STT,LLM,TTS pipeline. The example uses Deepseek for both.
4. Set api keys, see .env.example and create your own .env.local.
5. Open scrape_docs and replace `BASE_URL` with your own docs that you want to perform RAG on. Then run `python scrape_docs.py` to scrape a set of live docs based on a sitemap. Alternatively, manaually fill the `data` folder with txt files.
6. `pnpm dev` to launch the next js webapp, and visit http://localhost:3000 on your browser.
7. `python baseten_rag.py dev` to connect the voice agent to livekit cloud room
7. Click join call in the web app to join the same livekit cloud room as the voice agent.
8. Start chatting in real-time!

Credits: this project is adapted from Recipes from Livekit, specifically, https://github.com/livekit-examples/agent-starter-react.