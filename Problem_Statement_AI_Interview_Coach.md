# Problem Statement — AI Interview Coach

**Project Name:** AI Interview Coach  
**Team:** Parvesh (Semester IV)  
**Tech Stack:** Python · Streamlit · Gemini API · Tavily Search  
**Deployment:** Railway (https://ai-interview-coach-production-c5bc.up.railway.app)

---

## 1. Problem

Technical interview preparation is a major challenge for students and early-career developers. The core issues are:

- **No personalized feedback** — Most candidates practice with generic question banks that don't reflect their specific target company or role.
- **No real-time evaluation** — Mock interviews with peers or mentors are hard to schedule and inconsistent in quality.
- **No adaptive questioning** — Static question lists don't adjust based on how the candidate is performing.
- **No structured scoring** — Candidates have no objective measure of how they are doing across different skills like communication, technical depth, or problem-solving.

As a result, candidates go into real interviews underprepared, lack awareness of their weak areas, and miss out on role-specific preparation.

---

## 2. Who Is Affected

- College students preparing for campus placements
- Early-career developers applying for their first technical roles
- Anyone preparing for interviews at specific companies without a coach or mentor

---

## 3. Our Solution

We built an AI-powered interview coach that simulates a real technical interview using a 3-agent architecture:

**Agent 1 — Research Agent**  
Takes the candidate's target job role, company, experience level, and tech stack. Uses Tavily web search to find real job listings and company information, then uses Gemini to generate 10 tailored interview questions.

**Agent 2 — Interviewer Agent**  
Conducts the interview in a multi-turn conversation. Asks questions adaptively based on the candidate's responses, following up where needed, just like a real interviewer would.

**Agent 3 — Feedback Agent (LLM-as-Judge)**  
Scores each answer across 5 criteria: Technical Depth, Communication Clarity, Problem Solving, Behavioral (STAR method), and Confidence. After all 10 questions, generates a final report with a score, grade, strengths, areas to improve, and a hiring recommendation.

---

## 4. Why This Matters

| Without AI Interview Coach | With AI Interview Coach |
|---|---|
| Generic questions, not role-specific | Questions tailored to company + role |
| No feedback after practice | Scored feedback on every answer |
| Static question list | Adaptive multi-turn conversation |
| No final assessment | Hiring recommendation + improvement plan |

---

## 5. Impact

This tool gives any candidate — regardless of their college, network, or access to mentors — the ability to practice like they have a personal interview coach available 24/7. It levels the playing field for students from tier-2 and tier-3 colleges who lack access to coaching resources.

---

*Submitted as part of Semester IV project evaluation.*
