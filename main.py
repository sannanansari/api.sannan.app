from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import List
from groq import Groq
import os
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import instructor
from langfuse import observe, Langfuse
# from langfuse.langchain import CallbackHandler
from contextlib import asynccontextmanager
from enum import Enum

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(title="Sanan AI API", version="1.0.0", lifespan=lifespan)

load_dotenv()

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

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST"),
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
    
class TeaType(str, Enum):
    green = "Green Tea"
    black = "Black Tea"
    white = "White Tea"
    oolong = "Oolong Tea"
    herbal = "Herbal Tea"
    puerh = "Pu-erh Tea"
    yellow = "Yellow Tea"

class TeaClassify(BaseModel):
    name: str
    classifies_type: TeaType
    origin_region: str
    season: str

    
class TeaSentimentAnalysis(BaseModel):
    sentiment: str = Field(description="exactly: positive, negative, or neutral")
    rating: str = Field(description="numeric score like '4 out of 5'")
    key_notes: str = Field(description="comma separated descriptors")
    
class TeaSentimentRequest(BaseModel):
    review: str

allTea: List[Tea] = [];

@app.get("/")
def home():
    return {"status" : "ok"};

@app.post("/chat")
@observe(name="chat")
def chat(req: ChatRequest) -> ChatResponse:
    # trace = langfuse.trace(name="chat")
    # generation = trace.generation(
    #     name="groq-chat",
    #     model="llama-3.1-8b-instant",
    #     input=req.question,
    # )

    response = raw_client.chat.completions.create(
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
    answer = response.choices[0].message.content


    # generation.end(
    #     output=answer,
    #     usage={
    #         "input": response.usage.prompt_tokens,
    #         "output": response.usage.completion_tokens,
    #     }
    # )

    return ChatResponse(answer=answer)
    
@app.post("/chat/stream")
@observe(name="chat-stream")
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
@observe(name="tea-structured")
def get_tea_structured(tea_name: str):
    # trace = langfuse.trace(name="tea-structured")
    # generation = trace.generation(
    #     name="groq-tea-details",
    #     model="llama-3.1-8b-instant",
    #     input=tea_name,
    # )

    result = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a tea expert. Return structured details about teas. Be accurate and concise."
            },
            {"role": "user", "content": f"Give me details about {tea_name} tea."}
        ],
        response_model=TeaDetails,
    )

    # generation.end(output=result.model_dump())
    return result

@app.get("/tea_classifies/{tea_name}")
@observe(name="tea-classify")
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
@observe(name="tea-extractor")
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

@app.post("/getReviewSentiments")
@observe(name="review-sentiment")
def get_tea_sentiment(req: TeaSentimentRequest):
    result = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": """You are a sentiment analysis expert for tea reviews.
Return:
- sentiment: must be exactly 'positive', 'negative', or 'neutral'
- rating: numeric rating out of 5 as a string e.g. '4 out of 5'
- key_notes: comma separated descriptors e.g. 'smooth, earthy, calming'"""
            },
            {"role": "user", "content": f"Analyse this review: {req.review}"}
        ],
        response_model=TeaSentimentAnalysis,
    )
    return result

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

