# ✈️ Smart Travel Planner (AI Day Trip Planner)

A modern, responsive AI-powered Travel Planner web application built with **FastAPI**, **Groq Cloud API** (high-speed LLM inference), and a sleek single-page UI matching the clean White & Warm Yellow theme.

Fully optimized to **run locally** and **deploy seamlessly to Vercel**.

---

## 🌟 What was Updated & Fixed from the Original Project

1. **Fixed Model 404 Error (`llama-3.3-70b-versatile`)**:
   - The original Colab notebook crashed because `llama-3.3-70b-versatile` was not accessible on the Groq endpoint.
   - Updated to use active, high-speed Groq models (`qwen/qwen3.8-27b`) with automatic model fallback and custom model configuration via environment variables.

2. **Transitioned from Notebook to Production Web App**:
   - Replaced interactive CLI `input()` functions inside LangGraph with an asynchronous **FastAPI** backend and RESTful `/api/generate` endpoint.
   - Replaced heavy/incompatible Gradio server with a lightweight, responsive single-page web UI that runs without WebSocket server limitations and is 100% serverless-ready for **Vercel**.

3. **Retained & Upgraded the "White & Yellow" Theme**:
   - Matches the original Gradio theme (`Yntec/HaleyCH_Theme_White_Yellow`) with clean warm amber/yellow buttons, sunny accent badges, and rounded input cards.
   - Added interactive clickable quick-chips for popular destinations (Hyderabad, Tokyo, Paris, Rome, etc.) and interests (Street Food, History, Museums, Nature, etc.).
   - Added trip duration (Day Trip, Half Day, Weekend 2 Days, 3 Days) and pace selection (Relaxed, Balanced, Fast-paced).

4. **Rich Itinerary Output & PDF Download**:
   - Renders formatted Markdown with timeline icons (🌅 Morning, ☀️ Afternoon, 🌆 Evening, 🌙 Night, 🍽️ Must-Try Food, 💡 Pro Local Tips).
   - Direct **Download as PDF** button (`html2pdf.js`) with custom styled PDF branding header and clean print breaks.
   - One-click actions: **Copy to Clipboard**, **Print / Save as PDF**, and **Plan Another Trip**.

5. **Professional Interactive Animations**:
   - Ambient floating golden gradient orbs in the background.
   - Shimmer wave sweep across the primary action button.
   - Interactive live flight journey step sequencer during generation (analyzing sights, organizing timeline, handpicking delicacies, finalizing plan).
   - Staggered cascade fade-in-up animations for each itinerary section.
   - Clean, distraction-free branding and responsive single-page design.

---

## 📁 Project Structure

```
AI_PLANNER/
├── api/
│   └── index.py            # FastAPI serverless backend for Vercel & local
├── public/
│   ├── index.html          # Clean single-page UI (White & Yellow theme)
│   ├── style.css           # Modern stylesheet with responsive design
│   └── app.js              # Client-side dynamic interaction & API calls
├── .env                    # Environment variables (Groq API Key & Model)
├── .env.example            # Template for environment configuration
├── .gitignore              # Ignored files for clean git tracking
├── requirements.txt        # Production dependencies
├── run.py                  # One-click local development runner
├── vercel.json             # Vercel routing configuration
└── README.md               # Documentation & setup guide
```

---

## 🚀 Running Locally

The local server is already configured and running on `http://127.0.0.1:8000`.

To start or restart it anytime:

### Method 1: Using the created virtual environment (Recommended)
```powershell
.\.venv\Scripts\python.exe run.py
```

### Method 2: Using standard Python or UV
```powershell
# If using UV
uv run python run.py

# Or activate virtual environment and run:
.\.venv\Scripts\activate
python run.py
```

Then open your browser at **[http://localhost:8000](http://localhost:8000)**.

---

## 🌐 Deploying to Vercel

This repository is pre-configured for Vercel with `vercel.json`, `requirements.txt`, and `api/index.py`.

### Option A: Deploy via GitHub (Easiest)

1. Push this folder to a GitHub repository:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Smart Travel Planner"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

2. Go to [vercel.com](https://vercel.com) and click **"Add New Project"**.
3. Select your GitHub repository and click **"Import"**.
4. Under **Environment Variables**, add:
   - **`GROQ_API_KEY`**: `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` (or your own Groq key)
   - **`GROQ_MODEL`**: `qwen/qwen3.8-27b`
5. Click **"Deploy"**. Vercel will build the Python serverless function and publish your site with a live URL in seconds!

### Option B: Deploy via Vercel CLI

1. Open your terminal in this directory:
   ```powershell
   npx vercel
   ```
2. Follow the on-screen prompts to link and deploy.
3. Add your environment variables when prompted or run:
   ```powershell
   npx vercel env add GROQ_API_KEY
   ```
4. Deploy to production:
   ```powershell
   npx vercel --prod
   ```

---

## 🔑 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `GROQ_API_KEY` | Your Groq Cloud API Key | Pre-configured in `.env` |
| `GROQ_MODEL` | Active model on Groq | `qwen/qwen3.8-27b` |
| `PORT` | Local server port | `8000` |

---

## 🧪 Testing the API Endpoints

- **Health Check**: `GET http://localhost:8000/api/health`
- **Plan Itinerary**: `POST http://localhost:8000/api/generate`
  ```json
  {
    "city": "Hyderabad",
    "interests": "food, culture, history",
    "duration": "1 Day",
    "pace": "Balanced"
  }
  ```
