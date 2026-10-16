import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import httpx
from groq import Groq
from dotenv import load_dotenv

try:
    from api.pdf_generator import generate_itinerary_pdf
except ImportError:
    from pdf_generator import generate_itinerary_pdf

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Smart Travel Planner API",
    description="AI-powered trip itinerary generator supporting Gemini and Groq",
    version="1.2.0"
)

# CORS middleware for local testing and cross-origin deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def clean_key(key: Optional[str]) -> str:
    """Removes surrounding quotes and whitespace from API keys."""
    if not key:
        return ""
    return key.strip().strip("'\"").strip()


# Environment configuration
ENV_GEMINI_KEY = clean_key(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

DEFAULT_GROQ_API_KEY = clean_key(os.getenv(
    "GROQ_API_KEY",
    "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"
))
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()


class TripPlanRequest(BaseModel):
    city: str = Field(..., description="Destination city name", min_length=1)
    interests: str = Field(..., description="Comma-separated interests (e.g. food, history, photography)")
    duration: Optional[str] = Field("1 Day", description="Trip duration, e.g. 1 Day, 2 Days, 3 Days")
    pace: Optional[str] = Field("Balanced", description="Pace: Relaxed, Balanced, or Fast-paced")
    api_key: Optional[str] = Field(None, description="Optional custom Gemini or Groq API key")


class TripPlanResponse(BaseModel):
    success: bool
    city: str
    interests: List[str]
    duration: str
    pace: str
    itinerary: str
    model: str
    provider: str


def call_gemini(api_key: str, system_prompt: str, user_prompt: str, preferred_model: Optional[str] = None) -> Tuple[str, str]:
    """Generates itinerary using Google Gemini REST API."""
    models = [preferred_model or DEFAULT_GEMINI_MODEL, "gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    seen = set()
    models_to_try = [m for m in models if m and not (m in seen or seen.add(m))]

    last_error = None
    with httpx.Client(timeout=40.0) as client:
        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            
            # Format 1: With explicit systemInstruction
            body_with_sys = {
                "systemInstruction": {
                    "parts": [{"text": system_prompt}]
                },
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": user_prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }
            try:
                resp = client.post(url, json=body_with_sys)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            text = parts[0]["text"].strip()
                            if text:
                                return text, f"Gemini ({model})"
                
                # Format 2 fallback: Combined system + user prompt in contents
                body_fallback = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [{"text": f"{system_prompt}\n\nTask:\n{user_prompt}"}]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.7,
                        "maxOutputTokens": 2048
                    }
                }
                resp_fb = client.post(url, json=body_fallback)
                if resp_fb.status_code == 200:
                    data = resp_fb.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            text = parts[0]["text"].strip()
                            if text:
                                return text, f"Gemini ({model})"
                
                err_detail = resp_fb.text if resp_fb.status_code != 200 else resp.text
                last_error = f"Model {model} returned status {resp.status_code}: {err_detail[:200]}"
            except Exception as exc:
                last_error = f"Model {model} request failed: {str(exc)}"

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


def call_groq(api_key: str, system_prompt: str, user_prompt: str, preferred_model: Optional[str] = None) -> Tuple[str, str]:
    """Generates itinerary using Groq API."""
    client = Groq(api_key=api_key)
    candidate_models = [
        preferred_model or DEFAULT_GROQ_MODEL,
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile"
    ]
    seen = set()
    models_to_try = [m for m in candidate_models if m and not (m in seen or seen.add(m))]

    last_error = None
    for model_name in models_to_try:
        try:
            chat_completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2048,
            )
            content = chat_completion.choices[0].message.content
            if content and content.strip():
                return content.strip(), f"Groq ({model_name})"
        except Exception as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"All Groq models failed. Last error: {last_error}")


@app.get("/api/health")
@app.get("/health")
def health_check():
    gemini_ready = bool(ENV_GEMINI_KEY and not ENV_GEMINI_KEY.startswith("your_"))
    groq_ready = bool(DEFAULT_GROQ_API_KEY and not DEFAULT_GROQ_API_KEY.startswith("gsk_your_"))
    return {
        "status": "healthy",
        "gemini_configured": gemini_ready,
        "groq_configured": groq_ready,
        "primary_provider": "Gemini" if gemini_ready else "Groq",
        "default_model": DEFAULT_GEMINI_MODEL if gemini_ready else DEFAULT_GROQ_MODEL
    }


@app.post("/api/generate", response_model=TripPlanResponse)
@app.post("/generate", response_model=TripPlanResponse)
def generate_itinerary(req: TripPlanRequest):
    city = req.city.strip()
    if not city:
        raise HTTPException(status_code=400, detail="City name cannot be empty.")

    raw_interests = req.interests.strip()
    interests_list = [i.strip() for i in raw_interests.split(",") if i.strip()]
    if not interests_list:
        interests_list = ["Sightseeing", "Local Culture", "Food"]

    interests_str = ", ".join(interests_list)
    custom_key = clean_key(req.api_key)

    # Detailed travel planning prompts
    system_prompt = (
        "You are an expert, friendly travel guide and itinerary planner. "
        "Your goal is to create an inspiring, practical, and beautifully organized day trip itinerary "
        f"for {city} tailored to the user's specific interests: {interests_str}. "
        f"The user has selected a {req.duration} trip with a {req.pace} pace.\n\n"
        "Format the output in clean, readable Markdown with clear headings and bullet points:\n"
        "1. **🌟 Trip Overview**: Brief welcoming summary of what makes this day special.\n"
        "2. **🌅 Morning (8:30 AM - 12:00 PM)**: Kickoff activity, highlights, coffee/breakfast tip.\n"
        "3. **☀️ Afternoon (12:00 PM - 5:00 PM)**: Recommended authentic lunch spot, main sights matching interests.\n"
        "4. **🌆 Evening (5:00 PM - 8:00 PM)**: Golden hour walk, local market, sunset view.\n"
        "5. **🌙 Night (8:00 PM onwards)**: Memorable dinner recommendation & night vibes.\n"
        "6. **🍽️ Must-Try Local Delicacies**: 3-4 iconic local foods/drinks to taste.\n"
        "7. **💡 Pro Travel Tips**: Getting around (metro/cabs/walking), best photo spots, budget/safety advice.\n\n"
        "Keep the recommendations realistic in terms of travel time and geography within the city."
    )

    user_prompt = (
        f"Please create a personalized {req.duration} itinerary for my visit to {city}. "
        f"My interests are: {interests_str}. "
        f"Preferred pace: {req.pace}."
    )

    # Determine execution order based on keys
    itinerary_text = None
    used_model = None
    provider_name = None
    errors = []

    # 1. Custom key provided by user
    if custom_key:
        if custom_key.startswith("AIzaSy"):
            # User gave Gemini key
            try:
                itinerary_text, used_model = call_gemini(custom_key, system_prompt, user_prompt)
                provider_name = "Gemini"
            except Exception as e:
                errors.append(f"Custom Gemini key failed: {e}")
        elif custom_key.startswith("gsk_"):
            # User gave Groq key
            try:
                itinerary_text, used_model = call_groq(custom_key, system_prompt, user_prompt)
                provider_name = "Groq"
            except Exception as e:
                errors.append(f"Custom Groq key failed: {e}")
        else:
            # Try Gemini first, then Groq with the custom key
            try:
                itinerary_text, used_model = call_gemini(custom_key, system_prompt, user_prompt)
                provider_name = "Gemini"
            except Exception as e:
                errors.append(f"Custom key as Gemini failed: {e}")
                try:
                    itinerary_text, used_model = call_groq(custom_key, system_prompt, user_prompt)
                    provider_name = "Groq"
                except Exception as e2:
                    errors.append(f"Custom key as Groq failed: {e2}")

    # 2. If no custom key or custom key failed, use server environment keys
    if not itinerary_text:
        # Check Gemini environment key first if available
        if ENV_GEMINI_KEY and not ENV_GEMINI_KEY.startswith("your_"):
            try:
                itinerary_text, used_model = call_gemini(ENV_GEMINI_KEY, system_prompt, user_prompt)
                provider_name = "Gemini"
            except Exception as e:
                errors.append(f"Server Gemini failed: {e}")

        # Fallback to Groq
        if not itinerary_text and DEFAULT_GROQ_API_KEY:
            try:
                itinerary_text, used_model = call_groq(DEFAULT_GROQ_API_KEY, system_prompt, user_prompt)
                provider_name = "Groq"
            except Exception as e:
                errors.append(f"Server Groq failed: {e}")

    if not itinerary_text:
        combined_errors = " | ".join(errors) if errors else "No valid API key configured."
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate itinerary. {combined_errors}"
        )

    return TripPlanResponse(
        success=True,
        city=city,
        interests=interests_list,
        duration=req.duration or "1 Day",
        pace=req.pace or "Balanced",
        itinerary=itinerary_text,
        model=used_model or "AI Planner",
        provider=provider_name or "AI"
    )


class PdfDownloadRequest(BaseModel):
    city: str = Field("Trip", description="Destination city")
    duration: Optional[str] = Field("1 Day", description="Trip duration")
    interests: Optional[str] = Field("General", description="Interests")
    itinerary: str = Field(..., description="Generated itinerary markdown")


@app.post("/api/download-pdf")
@app.post("/download-pdf")
def download_itinerary_pdf(req: PdfDownloadRequest):
    if not req.itinerary or not req.itinerary.strip():
        raise HTTPException(status_code=400, detail="Itinerary content is empty.")

    try:
        pdf_bytes = generate_itinerary_pdf(
            city=req.city.strip() or "Destination",
            duration=req.duration or "1 Day",
            interests=req.interests or "General",
            itinerary_markdown=req.itinerary
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate PDF document: {str(e)}"
        )

    safe_city = re.sub(r'[^a-zA-Z0-9]', '_', req.city.strip() or "Trip")
    filename = f"{safe_city}_Day_Trip_Itinerary.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


# Serve public directory static files for local development
BASE_DIR = Path(__file__).resolve().parent.parent
PUBLIC_DIR = BASE_DIR / "public"

if PUBLIC_DIR.exists():
    @app.get("/")
    def serve_index():
        index_file = PUBLIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "Smart Travel Planner API is running. UI index.html not found."}

    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

    @app.get("/{full_path:path}")
    def serve_static(full_path: str):
        target = PUBLIC_DIR / full_path
        if target.exists() and target.is_file():
            return FileResponse(target)
        index_file = PUBLIC_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return JSONResponse({"detail": "Not found"}, status_code=404)
