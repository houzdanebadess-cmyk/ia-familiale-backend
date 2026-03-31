from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import os
import httpx
from datetime import datetime
import uuid
from typing import Optional

app = FastAPI()

# CORS pour permettre au frontend de communiquer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connexion Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# OpenRouter
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
    # Appel à OpenRouter
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "nousresearch/hermes-3-llama-3.1-8b:free",
                "messages": [
                    {"role": "user", "content": message.content}
                ]
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Erreur IA")
        
        ai_response = response.json()["choices"][0]["message"]["content"]
    
    # Sauvegarde dans Supabase
    conv_id = message.conversation_id
    if not conv_id:
        conv = supabase.table("conversations").insert({
            "user_id": message.user_id,
            "title": message.content[:50]
        }).execute()
        conv_id = conv.data[0]["id"]
    
    supabase.table("messages").insert([
        {
            "conversation_id": conv_id,
            "role": "user",
            "content": message.content,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "conversation_id": conv_id,
            "role": "assistant",
            "content": ai_response,
            "created_at": datetime.utcnow().isoformat()
        }
    ]).execute()
    
    return {
        "response": ai_response,
        "conversation_id": conv_id
    }

@app.get("/conversations/{user_id}")
async def get_conversations(user_id: str):
    result = supabase.table("conversations")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("created_at", desc=True)\
        .execute()
    return result.data

@app.get("/messages/{conversation_id}")
async def get_messages(conversation_id: str):
    result = supabase.table("messages")\
        .select("*")\
        .eq("conversation_id", conversation_id)\
        .order("created_at")\
        .execute()
    return result.data

@app.post("/register")
async def register(user_data: dict):
    user_id = str(uuid.uuid4())
    supabase.table("family_members").insert({
        "id": user_id,
        "name": user_data["name"],
        "email": user_data.get("email", f"{user_data['name']}@familial.com"),
        "password": user_data.get("password", "family123")
    }).execute()
    return {"user_id": user_id, "name": user_data["name"]}