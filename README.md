# 🎯 AI Interview Coach
### Real-Time Mock Interview Prep with 3 AI Agents

A fully deployed AI agent system that conducts real-time mock interviews using 3 specialized agents — built for Semester IV B.E. ECE End-Semester Project.

**[🚀 Live App on Railway](https://ai-interview-coach-production-c5bc.up.railway.app)** | **[📹 Watch Loom Demo](https://www.loom.com/share/acc38469f34e4410a15f46ee41075ce3)**

---

## 🤖 The 3 Agents

| Agent | Role | Tools Used |
|-------|------|------------|
| 🔍 **Research Agent** | Searches the web for real, current interview questions from your target company | Tavily Search + Gemini |
| 🎤 **Interviewer Agent** | Conducts a live adaptive mock interview — follows up on weak answers, moves on from strong ones | Gemini (multi-turn) |
| 📊 **Feedback & Judge Agent** | Scores every answer on 5 criteria, gives coaching tips, produces a final report | Gemini (LLM-as-Judge) |

---

## 🏗 Architecture

```
User Input (Role + Company + Level)
         ↓
🔍 Research Agent
   └─ Tavily Search → web results
   └─ Gemini → extract & structure question bank
         ↓
🎤 Interviewer Agent  (loop × 10 questions)
   └─ Gemini → adaptive question selection
   └─ Tracks conversation history
         ↓  (each answer)
📊 Feedback Agent
   └─ Gemini → score answer (1–10) on:
      · Technical Depth
      · Communication Clarity
      · Problem Solving
      · Behavioral Examples
      · Confidence & Presence
         ↓
📋 Final Report
   └─ Overall score, grade, hiring recommendation
   └─ Strengths, improvements, next steps
```

---

## ⚙️ Setup & Run Locally

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/ai-interview-coach
cd ai-interview-coach
pip install -r requirements.txt
```

### 2. Set API Keys
```bash
cp .env.example .env
# Edit .env and add your keys
```

Get your keys:
- **Gemini API Key** → https://aistudio.google.com/app/apikey (Free)
- **Tavily API Key** → https://tavily.com (Free tier available)

### 3. Run
```bash
streamlit run app.py
```

---

## 🚀 Deploy to Railway

1. Push to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables: `GEMINI_API_KEY` and `TAVILY_API_KEY`
4. Deploy! Railway auto-detects Streamlit.

Or deploy to **Vercel** with a `vercel.json` config.

---

## 📁 File Structure

```
interview_prep/
├── app.py          # Main Streamlit app + UI
├── agents.py       # All 3 AI agents
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🧪 LLM-as-Judge Rubric

The Feedback Agent evaluates each answer on:

| Criterion | What's Evaluated | Scale |
|-----------|-----------------|-------|
| Technical Depth | Correctness, specificity, knowledge breadth | 1–10 |
| Communication Clarity | Structure, conciseness, examples | 1–10 |
| Problem Solving | Approach, creativity, logical flow | 1–10 |
| Behavioral Examples | STAR method, relevance, specificity | 1–10 |
| Confidence & Presence | Tone, professionalism, conviction | 1–10 |

Final report includes: overall score, grade (A–F), hiring recommendation, strengths, improvements, and next steps.

---

## 👥 Team

- **Role A (Architect)** — Problem definition, architecture design, agent orchestration
- **Role B (Builder)** — Implementation, UI, deployment, Loom video

---

*Semester IV · B.E. Electronics & Communication · Introduction to Agentic AI Systems*
