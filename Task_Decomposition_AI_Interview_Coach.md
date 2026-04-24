# Task Decomposition & Spec Document — AI Interview Coach

**Project Name:** AI Interview Coach  
**Team:** Parvesh (Semester IV)  
**Tech Stack:** Python · Streamlit · Gemini API · Tavily Search  
**Deployment:** Railway

---

## 1. Project Overview

A 3-agent AI system that simulates a personalized technical interview. The user provides their target role, company, experience level, and tech stack. The system then conducts a full interview and returns a scored feedback report.

---

## 2. System Architecture Summary

```
User Input → Research Agent → Interviewer Agent → Feedback Agent → Final Report
```

Each agent is a separate module with a defined input, process, and output. Agents communicate by passing structured data (JSON / Python dicts) between each other.

---

## 3. Task Breakdown by Agent

---

### Agent 1 — Research Agent

**Goal:** Generate a tailored question bank based on the user's profile.

| Task | Description | Status |
|---|---|---|
| Collect user inputs | Job role, company, experience level, tech stack via Streamlit form | ✅ Done |
| Build Tavily search query | Combine inputs into a structured web search query | ✅ Done |
| Fetch web results | Use Tavily API to get job listings, company info, tech docs | ✅ Done |
| Synthesize with Gemini | Pass raw search results + user profile to Gemini with a structured prompt | ✅ Done |
| Generate question bank | Output a list of 10 tailored interview questions as structured JSON | ✅ Done |

**Input:** `{ role, company, experience_level, tech_stack }`  
**Output:** `{ questions: [ q1, q2, ... q10 ] }`

---

### Agent 2 — Interviewer Agent

**Goal:** Conduct a realistic multi-turn interview using the question bank.

| Task | Description | Status |
|---|---|---|
| Load question bank | Receive question list from Research Agent | ✅ Done |
| Present questions | Display each question to the candidate one at a time via Streamlit | ✅ Done |
| Capture candidate answers | Store each answer mapped to its question | ✅ Done |
| Adaptive follow-up | Use Gemini to generate follow-up questions based on weak or short answers | ✅ Done |
| Manage conversation state | Track which question is active, store full Q&A history | ✅ Done |
| Hand off to Feedback Agent | Pass complete Q&A pairs to next agent after all 10 questions | ✅ Done |

**Input:** `{ questions: [...] }`  
**Output:** `{ qa_pairs: [ { question, answer }, ... ] }`

---

### Agent 3 — Feedback Agent (LLM-as-Judge)

**Goal:** Score each answer and generate a final hiring report.

| Task | Description | Status |
|---|---|---|
| Receive Q&A pairs | Accept all question-answer pairs from Interviewer Agent | ✅ Done |
| Score per answer | Use Gemini to evaluate each answer on 5 criteria (see below) | ✅ Done |
| Aggregate scores | Calculate total score and assign a grade (A/B/C/D) | ✅ Done |
| Generate strengths | Identify top 2-3 things the candidate did well | ✅ Done |
| Generate improvements | Identify top 2-3 areas the candidate needs to work on | ✅ Done |
| Hiring recommendation | Output "Hire" / "No Hire" / "Maybe" based on overall score | ✅ Done |
| Render final report | Display full report in Streamlit UI | ✅ Done |

**Scoring Criteria (each out of 10):**

| Criteria | What It Measures |
|---|---|
| Technical Depth | Accuracy and depth of technical knowledge |
| Communication Clarity | How clearly and structured the answer is |
| Problem Solving | Approach to breaking down and solving problems |
| Behavioral (STAR) | Use of Situation-Task-Action-Result format |
| Confidence | Assertiveness and completeness of the answer |

**Input:** `{ qa_pairs: [ { question, answer }, ... ] }`  
**Output:** `{ scores, grade, strengths, improvements, recommendation, report_text }`

---

## 4. Frontend — Streamlit UI

| Task | Description | Status |
|---|---|---|
| Input form | Fields for role, company, experience level, tech stack | ✅ Done |
| Interview screen | Display question, text input for answer, next button | ✅ Done |
| Progress indicator | Show question X of 10 | ✅ Done |
| Report screen | Show scores, grade, strengths, improvements, recommendation | ✅ Done |
| Session state management | Maintain state across page interactions using `st.session_state` | ✅ Done |

---

## 5. Integration & Deployment

| Task | Description | Status |
|---|---|---|
| Gemini API integration | Connect all agents to Gemini via `google-generativeai` SDK | ✅ Done |
| Tavily API integration | Connect Research Agent to Tavily search API | ✅ Done |
| Environment variables | Store API keys in `.env` / Railway environment secrets | ✅ Done |
| Requirements file | `requirements.txt` with all dependencies | ✅ Done |
| Railway deployment | Deploy Streamlit app to Railway with public URL | ✅ Done |
| GitHub repo | Clean code pushed to public GitHub repository | ✅ Done |

---

## 6. Challenges Faced

| Challenge | How We Solved It |
|---|---|
| Tavily returning irrelevant results | Added role + company + "interview questions" as structured query keywords |
| Gemini giving inconsistent JSON output | Added strict output formatting instructions in the prompt + JSON parsing with error handling |
| Streamlit losing state between reruns | Used `st.session_state` to persist question index and answers |
| Deployment failing on Railway | Fixed by explicitly setting `PORT` env variable and updating start command in `railway.json` |

---

## 7. Future Scope

- Add a 4th "Devil's Advocate" agent that challenges weak answers with hostile follow-ups
- Implement streaming responses (token-by-token) for a more realistic interview feel
- Add a meta-feedback layer that tracks patterns across multiple sessions
- Voice input/output support for a fully realistic interview simulation

---

*Submitted as part of Semester IV project evaluation.*
