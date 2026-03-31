from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx
from typing import Optional
import uuid

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class Message(BaseModel):
    user_id: str
    content: str
    conversation_id: Optional[str] = None

@app.get("/")
def root():
    return {"message": "IA Familiale - API en ligne !"}

@app.post("/chat")
async def chat(message: Message):
    try:
        if not GEMINI_API_KEY:
            return {"response": "Erreur: Clé API Gemini manquante", "conversation_id": message.conversation_id}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [{
                        "parts": [{"text": message.content}]
                    }]
                }
            )
            
            if response.status_code != 200:
                return {
                    "response": f"Erreur Gemini: {response.status_code}", 
                    "conversation_id": message.conversation_id
                }
            
            result = response.json()
            ai_response = result["candidates"][0]["content"]["parts"][0]["text"]
            
            return {
                "response": ai_response,
                "conversation_id": message.conversation_id or str(uuid.uuid4())
            }
            
    except Exception as e:
        return {
            "response": f"Erreur: {str(e)}", 
            "conversation_id": message.conversation_id
        }

@app.get("/conversations/{user_id}")
async def get_conversations(user_id: str):
    return []

@app.get("/messages/{conversation_id}")
async def get_messages(conversation_id: str):
    return []

@app.post("/register")
async def register(user_data: dict):
    return {"user_id": str(uuid.uuid4()), "name": user_data.get("name", "Membre")}
