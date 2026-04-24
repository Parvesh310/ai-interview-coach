import os
import json
import time
from google import genai
from google.genai import types
from tavily import TavilyClient


def _call_with_retry(client, model, contents, config, retries=3):
    """Call Gemini with automatic retry on 429 rate limit errors."""
    for attempt in range(retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                wait = 30 * (attempt + 1)
                time.sleep(wait)
                if attempt == retries - 1:
                    raise
            else:
                raise

# ─────────────────────────────────────────────
# AGENT 1 — RESEARCH AGENT
# Fetches real interview questions via Tavily
# ─────────────────────────────────────────────

def research_agent(client: genai.Client, tavily: TavilyClient, role: str, company: str, level: str, log=None) -> dict:
    """Searches the web for real, current interview questions for the given role/company."""
    
    if log: log("🔍 Research Agent: Searching for real interview questions...")

    queries = [
        f"{company} {role} interview questions {level}",
    ]

    all_results = []
    for q in queries:
        results = tavily.search(query=q, max_results=3)
        for r in results.get("results", []):
            all_results.append(f"Source: {r['title']}\n{r['content'][:250]}")

    combined = "\n\n---\n\n".join(all_results)

    prompt = f"""You are an expert interview coach with deep knowledge of the tech industry.

Based on these real web search results about {company} {role} interviews:

{combined}

Extract and organize a comprehensive interview question bank for a {level} level {role} position at {company}.

Return ONLY valid JSON in this exact format:
{{
  "company": "{company}",
  "role": "{role}",
  "level": "{level}",
  "technical_questions": ["question1", "question2", "question3", "question4", "question5"],
  "behavioral_questions": ["question1", "question2", "question3", "question4"],
  "culture_fit_questions": ["question1", "question2", "question3"],
  "key_topics": ["topic1", "topic2", "topic3", "topic4"],
  "interview_tips": ["tip1", "tip2", "tip3"]
}}

Make questions specific, realistic and relevant to {company}'s known interview style."""

    response = _call_with_retry(
        client,
        model="gemini-1.5-flash",
        contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
        config=types.GenerateContentConfig(
            system_instruction="You are an expert interview research analyst. Always return valid JSON only, no markdown, no backticks."
        ),
    )

    raw = response.text.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    
    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"Warning: JSON parsing failed in research_agent! Error: {e}\nRaw output: {raw[:100]}")
        # fallback
        data = {
            "company": company, "role": role, "level": level,
            "technical_questions": [
                f"Explain your experience with key {role} technologies.",
                f"How would you design a scalable system for {company}?",
                "Walk me through a complex technical problem you solved.",
                "What's your approach to debugging a production issue?",
                "How do you ensure code quality in your projects?"
            ],
            "behavioral_questions": [
                "Tell me about a time you handled a conflict in your team.",
                "Describe a project where you had to meet a tight deadline.",
                "How do you prioritize tasks when everything feels urgent?",
                "Tell me about a time you failed and what you learned."
            ],
            "culture_fit_questions": [
                f"Why do you want to work at {company}?",
                "What does an ideal work environment look like for you?",
                "How do you stay updated with industry trends?"
            ],
            "key_topics": ["System Design", "Data Structures", "Problem Solving", "Leadership"],
            "interview_tips": [
                f"Research {company}'s recent products and news before the interview.",
                "Use the STAR method for behavioral questions.",
                "Prepare 2-3 questions to ask the interviewer."
            ]
        }

    if log: log(f"✅ Research Agent: Found {len(data.get('technical_questions', []))} technical + {len(data.get('behavioral_questions', []))} behavioral questions!")
    return data


# ─────────────────────────────────────────────
# AGENT 2 — INTERVIEWER AGENT
# Conducts a live, dynamic mock interview
# ─────────────────────────────────────────────

def interviewer_agent(
    client: genai.Client,
    question_bank: dict,
    conversation_history: list,
    user_answer: str,
    current_q_index: int,
    log=None
) -> dict:
    """Dynamic interviewer that adapts follow-up questions based on user answers."""

    role = question_bank.get("role", "Software Engineer")
    company = question_bank.get("company", "the company")
    level = question_bank.get("level", "mid")

    all_questions = (
        question_bank.get("technical_questions", []) +
        question_bank.get("behavioral_questions", []) +
        question_bank.get("culture_fit_questions", [])
    )

    questions_str = json.dumps(all_questions, indent=2)
    history_str = json.dumps(conversation_history[-6:], indent=2) if conversation_history else "[]"

    system_prompt = f"""You are a senior interviewer at {company} conducting a real interview for a {level} {role} position.

Your personality: Professional but warm. You probe deeper when answers are vague. You acknowledge good answers briefly. You keep the interview flowing naturally.

Rules:
- Ask ONE question at a time
- If the candidate's answer is shallow, ask a targeted follow-up
- If the answer is strong, move to the next question from the bank
- After 8-10 exchanges total, signal the interview is wrapping up
- Never repeat a question already asked
- Keep your response conversational and realistic"""

    prompt = f"""Question bank available:
{questions_str}

Recent conversation:
{history_str}

The candidate just answered question #{current_q_index}:
"{user_answer}"

Decide: Should you ask a follow-up (if answer was vague/incomplete) or move to the next question?

Return ONLY valid JSON:
{{
  "interviewer_response": "Your spoken response as the interviewer (acknowledge briefly + ask next question)",
  "next_question": "The exact question you are now asking",
  "question_type": "technical|behavioral|culture_fit|follow_up",
  "is_interview_complete": false,
  "questions_asked_count": {current_q_index + 1}
}}

If this is question 9 or 10, set is_interview_complete to true and wrap up naturally."""

    response = _call_with_retry(
        client,
        model="gemini-1.5-flash",
        contents=[
            *[types.Content(role="model" if m["role"] == "interviewer" else "user", parts=[types.Part.from_text(text=m["content"])]) for m in conversation_history[-4:]],
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        ],
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )

    raw = response.text.strip().replace("```json", "").replace("```", "").strip()
    
    try:
        result = json.loads(raw)
    except Exception as e:
        print(f"Warning: JSON parsing failed in interviewer_agent! Error: {e}\nRaw output: {raw[:100]}")
        result = {
            "interviewer_response": "That's interesting. Let me ask you something else.",
            "next_question": all_questions[min(current_q_index + 1, len(all_questions) - 1)],
            "question_type": "technical",
            "is_interview_complete": current_q_index >= 9,
            "questions_asked_count": current_q_index + 1
        }

    if log: log(f"🎤 Interviewer Agent: Asked question #{result.get('questions_asked_count', '?')} ({result.get('question_type', '')})")
    return result


# ─────────────────────────────────────────────
# AGENT 3 — FEEDBACK & JUDGE AGENT
# Scores answers and gives coaching
# ─────────────────────────────────────────────

def feedback_agent(
    client: genai.Client,
    question: str,
    answer: str,
    question_type: str,
    role: str,
    is_final: bool = False,
    full_conversation: list = None,
    log=None
) -> dict:
    """LLM-as-Judge: evaluates answer quality and provides coaching."""

    if log: log("📊 Feedback Agent: Evaluating your answer...")

    if is_final and full_conversation:
        # Final comprehensive evaluation
        conv_str = json.dumps(full_conversation, indent=2)
        prompt = f"""You are a senior {role} interview coach. Evaluate this complete mock interview.

Full conversation:
{conv_str}

Provide a comprehensive final evaluation. Return ONLY valid JSON:
{{
  "overall_score": 7.5,
  "overall_grade": "B+",
  "scores": {{
    "technical_depth": {{"score": 8, "reasoning": "..."}},
    "communication_clarity": {{"score": 7, "reasoning": "..."}},
    "problem_solving": {{"score": 8, "reasoning": "..."}},
    "behavioral_examples": {{"score": 6, "reasoning": "..."}},
    "confidence_presence": {{"score": 7, "reasoning": "..."}}
  }},
  "strengths": ["strength1", "strength2", "strength3"],
  "improvements": ["improvement1", "improvement2", "improvement3"],
  "hiring_recommendation": "Strong Yes | Yes | Maybe | No",
  "summary": "2-3 sentence overall assessment",
  "next_steps": ["action1", "action2", "action3"]
}}"""
    else:
        # Per-answer quick feedback
        prompt = f"""You are an expert {role} interview coach.

Question ({question_type}): "{question}"
Candidate's Answer: "{answer}"

Evaluate this specific answer. Return ONLY valid JSON:
{{
  "score": 7,
  "grade": "B",
  "quick_feedback": "2 sentence assessment of this answer",
  "what_worked": "What was good about this answer",
  "what_to_improve": "One specific thing to improve",
  "better_answer_hint": "A brief hint on how to structure a stronger answer",
  "used_star_method": true
}}

Score out of 10. Be specific and actionable."""

    response = _call_with_retry(
        client,
        model="gemini-1.5-flash",
        contents=[types.Content(role="user", parts=[types.Part.from_text(text=prompt)])],
        config=types.GenerateContentConfig(
            system_instruction="You are a strict but fair interview coach. Return only valid JSON, no markdown."
        ),
    )

    raw = response.text.strip().replace("```json", "").replace("```", "").strip()
    
    try:
        result = json.loads(raw)
    except Exception as e:
        print(f"Warning: JSON parsing failed in feedback_agent! Error: {e}\nRaw output: {raw[:100]}")
        if is_final:
            result = {
                "overall_score": 7.0, "overall_grade": "B",
                "scores": {
                    "technical_depth": {"score": 7, "reasoning": "Decent technical knowledge shown."},
                    "communication_clarity": {"score": 7, "reasoning": "Answers were mostly clear."},
                    "problem_solving": {"score": 7, "reasoning": "Good approach to problems."},
                    "behavioral_examples": {"score": 6, "reasoning": "Could use more specific examples."},
                    "confidence_presence": {"score": 7, "reasoning": "Came across as reasonably confident."}
                },
                "strengths": ["Clear communication", "Good technical knowledge", "Professional attitude"],
                "improvements": ["Add more specific examples", "Quantify achievements", "Practice STAR method"],
                "hiring_recommendation": "Yes",
                "summary": "Solid candidate with good fundamentals. Practice behavioral questions more.",
                "next_steps": ["Practice 5 more mock interviews", "Review system design concepts", "Prepare STAR stories"]
            }
        else:
            result = {
                "score": 6, "grade": "C+",
                "quick_feedback": "Decent answer but could be more specific.",
                "what_worked": "You addressed the question directly.",
                "what_to_improve": "Add concrete examples from your experience.",
                "better_answer_hint": "Use the STAR method: Situation, Task, Action, Result.",
                "used_star_method": False
            }

    if log: log(f"✅ Feedback Agent: Score {result.get('score', result.get('overall_score', '?'))}/10")
    return result
