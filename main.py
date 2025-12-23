import os
import logging
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
import requests
import json

from rag import RAGHandler
from woo_handler import WooCommerceHandler
from prompts import SYSTEM_PROMPT
from cache_handler import ResponseCache
from settings_manager import SettingsManager
from analytics_manager import AnalyticsManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Add CORS Middleware (Critical for ngrok and widget cross-origin requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize handlers
rag = RAGHandler()
woo = WooCommerceHandler()
settings_manager = SettingsManager()
analytics = AnalyticsManager()

# Initialize Groq client (OpenAI-compatible)
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
response_cache = ResponseCache(ttl_minutes=5)  # Cache responses for 5 minutes

# Model Configuration
MODEL_NAME = "llama-3.3-70b-versatile"  # Groq's best model for production

# ... (WATI Config remains same) ...

# ... (Startup event remains commented or we can uncomment it, but crawler handles ingestion now) ...

class TestMessage(BaseModel):
    message: str

@app.get("/")
def read_root():
    return {"status": "active", "service": "AI WhatsApp Commerce Bot (Live Only)"}

def send_whatsapp_message(wa_id: str, message: str):
    """
    Send a message back to the user via WATI API.
    """
    if not WATI_TOKEN:
        logger.error("WATI_TOKEN not set. Cannot send message.")
        return

    url = f"{WATI_API_ENDPOINT}/api/v1/sendSessionMessage/{wa_id}"
    headers = {
        "Authorization": f"Bearer {WATI_TOKEN}",
        "Content-Type": "application/json"
    }
    params = {
        "messageText": message
    }
    
    try:
        response = requests.post(url, headers=headers, params=params)
        response.raise_for_status()
        logger.info(f"Message sent to {wa_id}: {response.json()}")
    except Exception as e:
        logger.error(f"Failed to send message to {wa_id}: {e}")

# --- TOOL DEFINITIONS (Groq-Compatible) ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_store_products",
            "description": "Search for products in the WooCommerce store. If query is empty, returns the product catalog.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Product search keyword. Use empty string to list all products."
                    }
                },
                "required": []  # Make query optional for catalog listing
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Retrieve order details and status by order ID number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID as a string of digits"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search website content for educational information like ingredients, benefits, policies, or company info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search topic or question"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def generate_bot_response(user_message: str) -> str:
    """
    Core logic: Agentic Tool Use (MCP Style).
    The AI decides which tool to call based on the user message.
    """
    # 1. Check Cache First (Save API Calls)
    cached_response = response_cache.get(user_message)
    if cached_response:
        logger.info("💾 Returning cached response")
        return cached_response
    
    messages = [
        {"role": "system", "content": "You are a professional AI assistant for Roze BioHealth. Use the available tools to answer customer questions about products, orders, and general information accurately."},
        {"role": "user", "content": user_message}
    ]

    try:
        # 2. First Call: Let AI decide if it needs tools
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            parallel_tool_calls=False,  # Groq works better with sequential calls
            temperature=0.7,
            max_tokens=1024
        )
        
        response_message = completion.choices[0].message
        tool_calls = response_message.tool_calls

        # 3. If no tools needed, just return the text
        if not tool_calls:
            final_response = response_message.content
            response_cache.set(user_message, final_response)  # Cache it
            return final_response

        # 4. Process Tool Calls
        messages.append(response_message) # Add the assistant's "thought" (tool call request) to history

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            tool_output = ""
            
            logger.info(f"🤖 Executing Tool: {function_name} | Args: {args}")

            if function_name == "search_store_products":
                query = args.get("query", "")
                if not query:
                    products = woo.get_products() # Catalog
                else:
                    products = woo.get_products(search_term=query) # Search
                
                if products:
                    tool_output = "FOUND LIVE PRODUCTS:\n"
                    # Limit to 5
                    for p in products[:5]:
                        tool_output += woo.format_product_for_chat(p) + "\n---\n"
                else:
                    tool_output = "No products found."

            elif function_name == "check_order_status":
                order_id = args.get("order_id")
                order = woo.get_order_by_id(order_id)
                if order:
                    tool_output = f"ORDER STATUS:\nID: {order['id']}\nStatus: {order['status']}\nTotal: {order['currency']} {order['total']}\nItems: {order['line_items']}"
                else:
                    tool_output = "Order ID not found."

            elif function_name == "search_knowledge_base":
                query = args.get("query", "") # Default to empty string to avoid None crash
                if not query:
                    tool_output = "Please provide a topic to search."
                else:
                    docs = rag.query(query)
                    if docs:
                        tool_output = f"KNOWLEDGE BASE INFO:\n{docs}"
                    else:
                        tool_output = "No relevant info found in knowledge base."

            # Add tool result to conversation history
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(tool_output), # Ensure string
                }
            )

        # 5. Second Call: AI generates final answer using tool outputs
        final_completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages
        )
        
        final_response = final_completion.choices[0].message.content
        response_cache.set(user_message, final_response)  # Cache the final answer
        return final_response

    except Exception as e:
        error_str = str(e)
        logger.error(f"Agent Loop Error: {error_str}")
        
        # If Groq function calling failed, fall back to context injection method
        if "tool_use_failed" in error_str or "function" in error_str.lower():
            logger.warning("⚠️ Function calling failed. Falling back to context injection method.")
            try:
                # Fallback: Manually build context and ask without tools
                context = ""
                
                # Try to extract RAG context
                try:
                    docs = rag.query(user_message, n_results=3)
                    if docs:
                        if isinstance(docs, list):
                            context += "=== Knowledge Base ===\n" + "\n".join(docs) + "\n\n"
                        else:
                            context += f"=== Knowledge Base ===\n{docs}\n\n"
                except:
                    pass
                
                # Try to fetch products if it seems product-related
                msg_lower = user_message.lower()
                if any(word in msg_lower for word in ["product", "price", "buy", "stock", "have", "sell", "catalog"]):
                    try:
                        products = woo.get_products()
                        if products:
                            context += "=== Available Products ===\n"
                            for p in products[:5]:
                                context += woo.format_product_for_chat(p) + "\n---\n"
                    except:
                        pass
                
                # Simple completion without tools
                fallback_messages = [
                    {"role": "system", "content": "You are a professional assistant for Roze BioHealth. Answer customer questions based on the provided context."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_message}"}
                ]
                
                fallback_completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=fallback_messages,
                    temperature=0.7,
                    max_tokens=1024
                )
                
                return fallback_completion.choices[0].message.content
                
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return "I apologize, but I'm experiencing technical difficulties at the moment. Please try rephrasing your question or contact our support team directly."
        
        # For rate limit errors
        if "rate_limit" in error_str.lower():
            return "⏱️ Our AI is experiencing high demand right now. Please try again in a moment."
        
        # Generic professional error
        return "I apologize, but I'm having trouble processing your request right now. Please try again or contact our support team for immediate assistance."

def process_message(wa_id: str, user_message: str):
    """
    Orchestrator: 
    1. Send "Thinking" Status
    2. Generate Response (Heavy Lift)
    3. Send Final Answer
    """
    logger.info(f"Processing message from {wa_id}: {user_message}")
    
    # 1. Immediate Feedback (Professional "Thinking" State)
    # We can be smart about this: simple heuristics to guess intents for the status message
    lower_msg = user_message.lower()
    if "order" in lower_msg or "track" in lower_msg or "#" in lower_msg:
        status_msg = "🔍 Checking live order status, please wait a moment..."
    elif "price" in lower_msg or "stock" in lower_msg or "have" in lower_msg or "list" in lower_msg:
        status_msg = "🛒 Browsing our live catalog for you..."
    else:
        status_msg = "🤔 Analyzing your request..."
        
    send_whatsapp_message(wa_id, status_msg)

    # 2. Logic
    ai_response = generate_bot_response(user_message)
    
    # 3. Final Response
    send_whatsapp_message(wa_id, ai_response)

@app.post("/webhook")
async def wati_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming WATI webhooks.
    """
    try:
        payload = await request.json()
        logger.info(f"Received Webhook: {payload}")
        
        # WATI payload structure varies, handling common fields
        # Usually it's a list or a dict. Let's assume a dict for now.
        # Check if it's a message
        if "waId" in payload and "text" in payload:
            wa_id = payload["waId"]
            text = payload["text"]
            
            # Run processing in background to return 200 OK quickly
            background_tasks.add_task(process_message, wa_id, text)
            
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return {"status": "error", "message": str(e)}

# --- Local Test Interface ---

@app.post("/api/test-chat")
async def test_chat(message: TestMessage):
    """
    Endpoint for local testing without WhatsApp.
    """
    import time
    start_time = time.time()
    
    response = generate_bot_response(message.message)
    
    # Track analytics
    response_time_ms = int((time.time() - start_time) * 1000)
    analytics.track_conversation(message.message, response, response_time_ms)
    
    return {"response": response}

@app.get("/test", response_class=HTMLResponse)
async def test_interface():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Agent Test Interface</title>
        <style>
            body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            #chat-box { height: 400px; border: 1px solid #ccc; overflow-y: scroll; padding: 10px; margin-bottom: 10px; border-radius: 5px; }
            .message { margin-bottom: 10px; padding: 8px; border-radius: 5px; }
            .user { background-color: #e3f2fd; text-align: right; margin-left: 20%; }
            .bot { background-color: #f5f5f5; margin-right: 20%; }
            #input-area { display: flex; gap: 10px; }
            input { flex-grow: 1; padding: 10px; border-radius: 5px; border: 1px solid #ccc; }
            button { padding: 10px 20px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
        </style>
    </head>
    <body>
        <h1>🤖 AI Commerce Agent Test</h1>
        <div id="chat-box"></div>
        <div id="input-area">
            <input type="text" id="user-input" placeholder="Type a message..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Send</button>
        </div>

        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const chatBox = document.getElementById('chat-box');
                const text = input.value.trim();
                
                if (!text) return;

                // Add user message
                chatBox.innerHTML += `<div class="message user"><strong>You:</strong> ${text}</div>`;
                input.value = '';
                
                // Add Thinking Indicator
                const thinkingId = "thinking-" + Date.now();
                chatBox.innerHTML += `<div id="${thinkingId}" class="message bot" style="font-style:italic; color:#666;">🤔 AI is thinking...</div>`;
                chatBox.scrollTop = chatBox.scrollHeight;

                try {
                    const response = await fetch('/api/test-chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text })
                    });
                    const data = await response.json();
                    
                    // Remove thinking indicator
                    document.getElementById(thinkingId).remove();
                    
                    // Add bot message
                    // Convert newlines to <br> for display
                    const botText = data.response.replace(/\\n/g, '<br>');
                    chatBox.innerHTML += `<div class="message bot"><strong>Bot:</strong> ${botText}</div>`;
                } catch (error) {
                     // Remove thinking indicator
                    document.getElementById(thinkingId).remove();
                    chatBox.innerHTML += `<div class="message bot" style="color:red">Error: ${error.message}</div>`;
                }
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            function handleKeyPress(e) {
                if (e.key === 'Enter') sendMessage();
            }
        </script>
    </body>
    </html>
    """

# --- ADMIN PANEL API ROUTES ---

@app.get("/widget/chat-widget.js")
async def serve_widget_js():
    """Serve the chat widget JavaScript."""
    import os
    from fastapi.responses import FileResponse
    widget_js_path = os.path.join(os.path.dirname(__file__), "widget", "chat-widget.js")
    return FileResponse(widget_js_path, media_type="application/javascript")

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard():
    """Serve the admin dashboard."""
    import os
    admin_html_path = os.path.join(os.path.dirname(__file__), "admin", "dashboard.html")
    with open(admin_html_path, 'r', encoding='utf-8') as f:
        return HTMLResponse(content=f.read())

@app.get("/admin/settings")
async def get_settings():
    """Get all current settings."""
    return settings_manager.get_all_settings()

@app.post("/admin/settings")
async def update_settings(settings: Dict[str, Any]):
    """Update settings."""
    try:
        settings_manager.update_settings(settings)
        return {"status": "success", "message": "Settings updated successfully"}
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/admin/settings/reset")
async def reset_settings():
    """Reset settings to defaults."""
    try:
        settings_manager.reset_to_defaults()
        return {"status": "success", "message": "Settings reset to defaults"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/analytics/stats")
async def get_analytics_stats():
    """Get analytics dashboard statistics."""
    return analytics.get_dashboard_stats()

@app.post("/api/analytics/track")
async def track_analytics(data: Dict[str, Any]):
    """Track a conversation for analytics."""
    analytics.track_conversation(
        data.get("user_message", ""),
        data.get("bot_response", ""),
        0
    )
    return {"status": "tracked"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
