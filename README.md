# AI WhatsApp Commerce Bot

This is a FastAPI-based backend for an AI-powered WhatsApp Commerce Assistant.
It integrates WATI (WhatsApp API), OpenAI (GPT-4o), ChromaDB (RAG), and WooCommerce.

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Copy `.env` and fill in your API keys:
    ```bash
    OPENAI_API_KEY=sk-...
    WATI_TOKEN=...
    WATI_API_ENDPOINT=https://live-server-XXXX.wati.io
    WOO_URL=...
    WOO_KEY=...
    WOO_SECRET=...
    ```

3.  **Run the Server**:
    ```bash
    uvicorn main:app --reload --port 8001
    ```
    The server will start at `http://localhost:8001`.

4.  **Expose to Internet (for WATI Webhook)**:
    Use ngrok to expose your local server:
    ```bash
    ngrok http 8001
    ```
    Copy the HTTPS URL (e.g., `https://xyz.ngrok.io`) and set it as the Webhook URL in your WATI dashboard (append `/webhook`).
    Example: `https://xyz.ngrok.io/webhook`

## Features

-   **RAG (Retrieval Augmented Generation)**: Automatically ingests `data/products.txt` and `data/faqs.txt` on startup.
-   **WooCommerce Integration**: Fetches product data (mocked or live if credentials provided).
-   **WATI Integration**: Receives messages and sends responses via WhatsApp.
-   **AI Logic**: Uses GPT-4o to generate friendly, sales-aware responses based on the context.

## Project Structure

-   `main.py`: Entry point, FastAPI app, Webhook handler.
-   `rag.py`: ChromaDB vector store logic.
-   `woo_handler.py`: WooCommerce API interaction.
-   `prompts.py`: System prompt for the AI.
-   `data/`: Text files for RAG context.
