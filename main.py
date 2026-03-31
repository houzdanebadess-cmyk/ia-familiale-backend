from fastapi import FastAPI, HTTPException
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

# Récupérer les variables d'environnement
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

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
        # Vérifier que la clé existe
        if not OPENROUTER_API_KEY:
            return {"response": "Erreur: Clé API OpenRouter manquante", "conversation_id": message.conversation_id}
        
        # Préparer la requête pour OpenRouter
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "qwen/qwen-2.5-7b-instruct:free",
                    "messages": [
                        {
                            "role": "user",
                            "content": message.content
                        }
                    ]
                }
            )
            
            # Vérifier la réponse
            if response.status_code != 200:
                return {
                    "response": f"Erreur OpenRouter ({response.status_code}): {response.text[:200]}", 
                    "conversation_id": message.conversation_id
                }
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
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
