from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List
from groq import Groq
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import instructor

load_dotenv()

app = FastAPI();
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "https://ai.sannan.app",
        "https://ai-chat.asannan822.workers.dev",
        "https://ai-chat.sannan.app"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

raw_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
client = instructor.from_groq(
    Groq(api_key=os.getenv("GROQ_API_KEY")),
    mode=instructor.Mode.JSON,
)

class ChatRequest(BaseModel):
    question: str
    
class ChatResponse(BaseModel):
    answer: str

class Tea(BaseModel):
    id: int
    name: str
    origin: str
    
class TeaDetails(BaseModel):
    name: str
    origin: str
    flavour_profile: str
    caffeine_level:str
    best_served: str
    fun_fact: str
    
class TeaClassify(BaseModel):
    name: str
    classifies_type: str
    origin_region: str
    season: str
    
class TeaSentimentAnalysis(BaseModel):
    sentiment: str
    rating: str
    key_notes: str
    
class TeaSentimentRequest(BaseModel):
    review: str

allTea: List[Tea] = [];

@app.get("/")
def home():
    return {"status" : "ok"};

@app.post("/chat")
def chat(req: ChatRequest) -> ChatResponse:
    stream = raw_client.chat.completions.create(
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
            ] )
    return ChatResponse(answer=stream.choices[0].message.content)
    
@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    def generate():
        stream = raw_client.chat.completions.create(
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

@app.get("/tea-structured/{tea_name}")
def getTeaInStructure(tea_name: str):
    result = client.chat.completions.create(
        model="llama-3.1-8b-instant",
                messages=[
            {
                "role": "system",
                "content": "You are a tea expert. Return structured details about teas. Be accurate and concise."
            },
            {
                "role": "user",
                "content": f"Give me details about {tea_name} tea."
            }
        ],
        response_model=TeaDetails
    )
    return result;

@app.get("/tea_classifies/{tea_name}")
def getTeaClassifies(tea_name: str):
    result = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages= [
            {"role": "system","content": "You are a tea expert. Return structured details about teas. Be accurate and concise."},
            {"role": "user", "content": f"give me details about {tea_name} tea"}
        ],
        response_model=TeaClassify
    )
    return result;

@app.post("/teaextractor")
def getTeaDetailsFromText(teaText: TeaSentimentRequest):
    result = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages = [
        {"role": "system","content": "You are a best tea review. Return structured details about tea details in text. Be accurate and concise."},
        {"role": "user", "content": f"review: {teaText.review}"}
        ],
        response_model=TeaDetails

    )
    
    return result;

@app.post('/getReviewSentiments')
def getTeaSentiment(sentiment:TeaSentimentRequest):
    result = client.chat.completions.create(
        model='llama-3.1-8b-instant',
        messages = [
        {"role": "system","content": "You are a sentiment anaylsis review. Return structured details about review. Be accurate and concise."},
        {"role": "user", "content": f"review: {sentiment.review}"}
        ],
        response_model=TeaSentimentAnalysis
    )
    return result;

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

