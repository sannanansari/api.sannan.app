from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List
from groq import Groq
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI();
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "https://ai.sannan.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ChatRequest(BaseModel):
    question: str
    
class ChatResponse(BaseModel):
    answer: str

class Tea(BaseModel):
    id: int
    name: str
    origin: str

allTea: List[Tea] = [];

@app.get("/")
def home():
    return {"status" : "ok"};

@app.post("/chat")
def chat(req: ChatRequest) -> ChatResponse:
    stream = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {       
             "role": "system",
        "content": "You are a concise technical assistant. Answer in plain language. Maximum 3 sentences."
},
            {
                "role": "user",
                "content": req.question
            }
            
            ]    )
    return ChatResponse(answer=stream.choices[0].message.content)
    
@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    def generate():
        stream = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
            {"role": "system", "content": "You are a concise technical assistant."},
            {"role": "user", "content": req.question}
            ],
            stream= True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    return StreamingResponse(generate(),media_type="text/plain")


@app.get("/getAllTea")
def getAllTea():
    return allTea;

@app.post("/addTea")
def postNewTea(tea: Tea):
    allTea.append(tea)
    return tea;

@app.put("/updateTea/{tea_id}")
def updateATea(tea_id: int, updated_tea: Tea):
    for id,tea in enumerate(allTea):
        if tea.id == tea_id:
            allTea[id] = updated_tea;
            return updated_tea;
    raise HTTPException(status_code=404, detail="Tea not found")

@app.delete("/deleteTea/{tea_id}")
def deleteATea(tea_id: int):
    for id,tea in enumerate(allTea):
        if tea.id == tea_id:
            allTea.pop(id);
            return {"message": "Tea Deleted"}
    return {"error": "Tea not found"};

