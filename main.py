from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from anthropic import Anthropic
from pydantic import BaseModel
import asyncio
from typing import AsyncGenerator

app = FastAPI()
client = Anthropic()


class ChatRequest(BaseModel):
    message: str


async def stream_response(request: ChatRequest) -> AsyncGenerator[str, None]:
    try:
        with client.messages.stream(
            max_tokens=1024,
            messages=[{"role": "user", "content": request.message}],
            model="claude-3-5-sonnet-20241022",
        ) as stream:
            for text in stream.text_stream:
                # Yield each chunk of text
                yield text

    except Exception as e:
        yield f"Error: {str(e)}"


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(stream_response(request), media_type="text/plain")


@app.get("/", response_class=HTMLResponse)
async def get_index():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Claude Chat Stream</title>
        <style>
            body {
                max-width: 800px;
                margin: 20px auto;
                padding: 0 20px;
                font-family: Arial, sans-serif;
            }
            #response {
                white-space: pre-wrap;
                border: 1px solid #ccc;
                padding: 10px;
                margin-top: 20px;
                min-height: 200px;
                border-radius: 4px;
            }
            #message {
                width: 100%;
                margin-bottom: 10px;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            button {
                padding: 8px 16px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #0056b3;
            }
        </style>
    </head>
    <body>
        <h1>Claude Chat Stream</h1>
        <textarea id="message" rows="4" placeholder="Type your message here..."></textarea><br>
        <button onclick="sendMessage()">Send</button>
        <div id="response"></div>

        <script>
            async function sendMessage() {
                const message = document.getElementById('message').value;
                if (!message.trim()) return;
                
                const response = document.getElementById('response');
                response.textContent = '';
                
                try {
                    const res = await fetch('/chat/stream', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ message: message })
                    });
                    
                    if (!res.ok) {
                        throw new Error(`HTTP error! status: ${res.status}`);
                    }
                    
                    const reader = res.body.getReader();
                    const decoder = new TextDecoder();
                    
                    while (true) {
                        const { value, done } = await reader.read();
                        if (done) break;
                        
                        const text = decoder.decode(value);
                        response.textContent += text;
                    }
                } catch (error) {
                    console.error('Request failed:', error);
                    response.textContent = `Error: ${error.message}`;
                }
            }
            
            // Allow Enter key to send message
            document.getElementById('message').addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
