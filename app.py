import streamlit as st
import os
import time
from google import genai
from tavily import TavilyClient
from agents import research_agent, interviewer_agent, feedback_agent

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg: #0a0a0f;
    --surface: #111118;
    --surface2: #1a1a24;
    --border: #2a2a3a;
    --accent: #6c63ff;
    --accent2: #ff6584;
    --green: #00d9a0;
    --yellow: #ffd166;
    --text: #e8e8f0;
    --muted: #8888aa;
}

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
    background-color: var(--bg);
    color: var(--text);
}

.stApp { background: var(--bg); }

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}

/* Cards */
.agent-card {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem;
    margin: 0.5rem 0;
    transition: border-color 0.2s;
}
.agent-card.active { border-color: var(--accent); }
.agent-card.done { border-color: var(--green); }

/* Score badges */
.score-badge {
    display: inline-block;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85rem;
}
.score-high { background: rgba(0,217,160,0.15); color: var(--green); }
.score-mid  { background: rgba(255,209,102,0.15); color: var(--yellow); }
.score-low  { background: rgba(255,101,132,0.15); color: var(--accent2); }

/* Chat bubbles */
.chat-interviewer {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px 12px 12px 2px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0;
    max-width: 80%;
}
.chat-user {
    background: rgba(108,99,255,0.15);
    border: 1px solid rgba(108,99,255,0.3);
    border-radius: 12px 12px 2px 12px;
    padding: 1rem 1.2rem;
    margin: 0.5rem 0 0.5rem auto;
    max-width: 80%;
    text-align: right;
}

/* Buttons */
.stButton > button {
    background: var(--accent) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #7c74ff !important;
    transform: translateY(-1px);
}

/* Inputs */
.stTextInput input, .stSelectbox select, .stTextArea textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* Progress */
.stProgress > div > div {
    background: var(--accent) !important;
}

/* Metric */
[data-testid="stMetricValue"] {
    color: var(--accent) !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Headers */
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; }

/* Divider */
hr { border-color: var(--border) !important; }

/* Hide streamlit branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "phase": "setup",           # setup → researching → interviewing → complete
        "question_bank": None,
        "conversation": [],         # [{role, content, feedback}]
        "current_q_index": 0,
        "current_question": "",
        "current_q_type": "",
        "is_complete": False,
        "final_report": None,
        "logs": [],
        "scores": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────
# API CLIENTS — keys loaded from .env only
# ─────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
TAVILY_KEY = os.getenv("TAVILY_API_KEY", "")

@st.cache_resource
def get_clients():
    client = genai.Client(api_key=GEMINI_KEY, vertexai=False)
    tavily = TavilyClient(api_key=TAVILY_KEY)
    return client, tavily


def add_log(msg):
    st.session_state.logs.append(msg)


# ─────────────────────────────────────────────
# SIDEBAR — no API key inputs, clean UI
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 AI Interview Coach")
    st.markdown("---")
    
    # Show connection status
    gemini_ok = "✅" if GEMINI_KEY else "❌"
    tavily_ok = "✅" if TAVILY_KEY else "❌"
    st.markdown(f"{gemini_ok} Gemini API")
    st.markdown(f"{tavily_ok} Tavily Search")
    
    st.markdown("---")
    
    # Agent status
    st.markdown("### 🤖 Agent Status")
    
    phases = {
        "setup": 0, "researching": 1, "interviewing": 2, "complete": 3
    }
    current_phase = phases.get(st.session_state.phase, 0)
    
    agents = [
        ("🔍", "Research Agent", "Fetches real questions via Tavily"),
        ("🎤", "Interviewer Agent", "Conducts adaptive mock interview"),
        ("📊", "Feedback Agent", "Scores & coaches your answers"),
    ]
    
    for i, (icon, name, desc) in enumerate(agents):
        status = "done" if current_phase > i + 1 else ("active" if current_phase == i + 1 else "")
        indicator = "✅" if status == "done" else ("🟡" if status == "active" else "⚪")
        st.markdown(f"{indicator} **{name}**  \n<small style='color:#8888aa'>{desc}</small>", 
                    unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Logs
    if st.session_state.logs:
        st.markdown("### 📋 Activity Log")
        for log in st.session_state.logs[-6:]:
            st.markdown(f"<small style='color:#8888aa'>{log}</small>", unsafe_allow_html=True)
    
    if st.button("🔄 Start Over", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ─────────────────────────────────────────────
# PHASE 1 — SETUP
# ─────────────────────────────────────────────
if st.session_state.phase == "setup":
    
    st.markdown("# 🎯 AI Interview Coach")
    st.markdown("##### Real-time mock interviews powered by 3 AI agents")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### Your Target Role")
        company = st.text_input("Company", placeholder="Google, Amazon, Microsoft, Startup...")
        role = st.text_input("Role", placeholder="Software Engineer, Data Scientist, PM...")
        level = st.selectbox("Experience Level", 
                             ["Entry Level (0-2 yrs)", "Mid Level (2-5 yrs)", 
                              "Senior Level (5+ yrs)", "Lead / Staff"])
        interview_type = st.multiselect("Focus Areas", 
                                         ["Technical", "Behavioral", "System Design", "Culture Fit"],
                                         default=["Technical", "Behavioral"])
    
    with col2:
        st.markdown("### How It Works")
        steps = [
            ("🔍", "Research Agent", "Searches the web for real questions from your target company"),
            ("🎤", "Interviewer Agent", "Conducts a live adaptive mock interview (10 questions)"),
            ("📊", "Feedback Agent", "Scores each answer + gives a final coaching report"),
        ]
        for icon, title, desc in steps:
            st.markdown(f"""
<div class="agent-card">
<strong>{icon} {title}</strong><br>
<span style="color: #8888aa; font-size: 0.9rem">{desc}</span>
</div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🚀 Start Interview Prep", use_container_width=True):
        if not GEMINI_KEY or not TAVILY_KEY:
            st.error("⚠️ API keys not found. Please add them to your .env file.")
        elif not company or not role:
            st.error("⚠️ Please enter a company and role.")
        else:
            st.session_state.phase = "researching"
            st.session_state.company = company
            st.session_state.role = role
            st.session_state.level = level.split(" (")[0]
            st.rerun()


# ─────────────────────────────────────────────
# PHASE 2 — RESEARCHING
# ─────────────────────────────────────────────
elif st.session_state.phase == "researching":
    
    st.markdown(f"# 🔍 Researching {st.session_state.company} Interview Questions")
    
    with st.spinner("Agent 1 is searching the web for real interview questions..."):
        progress = st.progress(0)
        
        try:
            client, tavily = get_clients()
            
            add_log(f"🔍 Searching {st.session_state.company} {st.session_state.role} interviews...")
            progress.progress(30)
            
            question_bank = research_agent(
                client, tavily,
                st.session_state.role,
                st.session_state.company,
                st.session_state.level,
                log=add_log
            )
            
            progress.progress(100)
            st.session_state.question_bank = question_bank
            
        except Exception as e:
            st.error(f"Error: {e}")
            st.stop()
    
    # Show what was found
    qb = st.session_state.question_bank
    
    st.success(f"✅ Found questions! Ready to start your mock interview.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Technical Questions", len(qb.get("technical_questions", [])))
    col2.metric("Behavioral Questions", len(qb.get("behavioral_questions", [])))
    col3.metric("Culture Fit Questions", len(qb.get("culture_fit_questions", [])))
    
    with st.expander("📋 Preview Questions Found", expanded=False):
        tabs = st.tabs(["🔧 Technical", "💬 Behavioral", "🏢 Culture Fit", "💡 Tips"])
        
        with tabs[0]:
            for i, q in enumerate(qb.get("technical_questions", []), 1):
                st.markdown(f"**{i}.** {q}")
        with tabs[1]:
            for i, q in enumerate(qb.get("behavioral_questions", []), 1):
                st.markdown(f"**{i}.** {q}")
        with tabs[2]:
            for i, q in enumerate(qb.get("culture_fit_questions", []), 1):
                st.markdown(f"**{i}.** {q}")
        with tabs[3]:
            for tip in qb.get("interview_tips", []):
                st.markdown(f"💡 {tip}")
    
    st.markdown("---")
    
    if st.button("🎤 Begin Mock Interview", use_container_width=True):
        # Set first question
        first_q = qb.get("technical_questions", ["Tell me about yourself."])[0]
        st.session_state.current_question = first_q
        st.session_state.current_q_type = "technical"
        st.session_state.phase = "interviewing"
        add_log("🎤 Interview started!")
        st.rerun()


# ─────────────────────────────────────────────
# PHASE 3 — INTERVIEWING
# ─────────────────────────────────────────────
elif st.session_state.phase == "interviewing":
    
    qb = st.session_state.question_bank
    
    # Header with progress
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"### 🎤 Mock Interview — {qb.get('company')} · {qb.get('role')}")
    with col2:
        q_count = st.session_state.current_q_index + 1
        st.metric("Question", f"{q_count}/10")
    with col3:
        avg_score = sum(st.session_state.scores) / len(st.session_state.scores) if st.session_state.scores else 0
        st.metric("Avg Score", f"{avg_score:.1f}/10" if avg_score else "—")
    
    st.progress(st.session_state.current_q_index / 10)
    st.markdown("---")
    
    # Chat history
    for msg in st.session_state.conversation:
        if msg["role"] == "interviewer":
            st.markdown(f"""
<div class="chat-interviewer">
🎤 <strong>Interviewer</strong><br>{msg["content"]}
</div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
<div class="chat-user">
<strong>You</strong> 🧑<br>{msg["content"]}
</div>""", unsafe_allow_html=True)
            
            # Show inline feedback if exists
            if msg.get("feedback"):
                fb = msg["feedback"]
                score = fb.get("score", 0)
                grade = fb.get("grade", "")
                color = "score-high" if score >= 8 else ("score-mid" if score >= 6 else "score-low")
                
                with st.expander(f"📊 Feedback — Score: {score}/10 ({grade})", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"✅ **What worked:** {fb.get('what_worked', '')}")
                    with col2:
                        st.markdown(f"⚡ **Improve:** {fb.get('what_to_improve', '')}")
                    st.info(f"💡 **Hint:** {fb.get('better_answer_hint', '')}")
    
    # Current question
    if not st.session_state.is_complete:
        st.markdown("---")
        
        q_type_emoji = {"technical": "🔧", "behavioral": "💬", "culture_fit": "🏢", "follow_up": "🔄"}
        emoji = q_type_emoji.get(st.session_state.current_q_type, "❓")
        
        st.markdown(f"""
<div class="agent-card active">
{emoji} <strong>Current Question ({st.session_state.current_q_type.replace('_', ' ').title()})</strong><br><br>
<span style="font-size: 1.1rem">{st.session_state.current_question}</span>
</div>""", unsafe_allow_html=True)
        
        user_answer = st.text_area(
            "Your Answer",
            placeholder="Type your answer here... Be detailed and use examples from your experience.",
            height=150,
            key=f"answer_{st.session_state.current_q_index}"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            submit = st.button("📤 Submit Answer", use_container_width=True)
        with col2:
            skip = st.button("⏭️ Skip", use_container_width=True)
        
        if submit and user_answer.strip():
            try:
                client, tavily = get_clients()
                
                # Add to conversation
                st.session_state.conversation.append({
                    "role": "interviewer",
                    "content": st.session_state.current_question
                })
                
                with st.spinner("Agents processing..."):
                    # Agent 3: Get feedback on this answer
                    add_log(f"📊 Evaluating answer #{st.session_state.current_q_index + 1}...")
                    feedback = feedback_agent(
                        client,
                        st.session_state.current_question,
                        user_answer,
                        st.session_state.current_q_type,
                        qb.get("role", ""),
                        log=add_log
                    )
                    
                    st.session_state.scores.append(feedback.get("score", 6))
                    
                    # Add user answer with feedback
                    st.session_state.conversation.append({
                        "role": "user",
                        "content": user_answer,
                        "feedback": feedback
                    })
                    
                    # Agent 2: Get next question
                    add_log(f"🎤 Getting next question...")
                    interviewer_result = interviewer_agent(
                        client,
                        qb,
                        st.session_state.conversation,
                        user_answer,
                        st.session_state.current_q_index,
                        log=add_log
                    )
                
                st.session_state.current_q_index += 1
                
                if interviewer_result.get("is_interview_complete") or st.session_state.current_q_index >= 10:
                    st.session_state.is_complete = True
                    st.session_state.phase = "complete"
                    add_log("🏁 Interview complete! Generating final report...")
                else:
                    st.session_state.current_question = interviewer_result.get("next_question", "")
                    st.session_state.current_q_type = interviewer_result.get("question_type", "technical")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"Error: {e}")
        
        elif submit and not user_answer.strip():
            st.warning("Please type your answer first!")
        
        if skip:
            st.session_state.current_q_index += 1
            if st.session_state.current_q_index >= 10:
                st.session_state.phase = "complete"
                st.session_state.is_complete = True
            else:
                all_q = qb.get("technical_questions", []) + qb.get("behavioral_questions", [])
                idx = min(st.session_state.current_q_index, len(all_q) - 1)
                st.session_state.current_question = all_q[idx]
            st.rerun()


# ─────────────────────────────────────────────
# PHASE 4 — COMPLETE / FINAL REPORT
# ─────────────────────────────────────────────
elif st.session_state.phase == "complete":
    
    qb = st.session_state.question_bank
    
    # Generate final report if not done
    if not st.session_state.final_report:
        with st.spinner("📊 Feedback Agent generating your final evaluation..."):
            try:
                client, tavily = get_clients()
                add_log("📊 Generating comprehensive final report...")
                
                final_report = feedback_agent(
                    client,
                    question="", answer="",
                    question_type="final",
                    role=qb.get("role", ""),
                    is_final=True,
                    full_conversation=st.session_state.conversation,
                    log=add_log
                )
                st.session_state.final_report = final_report
                
            except Exception as e:
                st.error(f"Error generating report: {e}")
                st.stop()
    
    report = st.session_state.final_report
    
    # ── FINAL REPORT UI ──
    st.markdown(f"# 🏆 Interview Complete!")
    st.markdown(f"##### {qb.get('company')} · {qb.get('role')} · {qb.get('level')}")
    st.markdown("---")
    
    # Top metrics
    overall = report.get("overall_score", 0)
    grade = report.get("overall_grade", "B")
    recommendation = report.get("hiring_recommendation", "Yes")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Overall Score", f"{overall}/10")
    col2.metric("Grade", grade)
    col3.metric("Questions", len(st.session_state.scores))
    col4.metric("Recommendation", recommendation)
    
    st.markdown("---")
    
    # Score breakdown
    st.markdown("### 📊 Detailed Scores (LLM-as-Judge)")
    
    scores_data = report.get("scores", {})
    for criterion, data in scores_data.items():
        score = data.get("score", 0)
        reasoning = data.get("reasoning", "")
        label = criterion.replace("_", " ").title()
        color = "#00d9a0" if score >= 8 else ("#ffd166" if score >= 6 else "#ff6584")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown(f"**{label}**  \n`{score}/10`")
            st.progress(score / 10)
        with col2:
            st.markdown(f"<small style='color:#8888aa'>{reasoning}</small>", unsafe_allow_html=True)
        st.markdown("")
    
    st.markdown("---")
    
    # Strengths & Improvements
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Your Strengths")
        for s in report.get("strengths", []):
            st.markdown(f"✅ {s}")
    
    with col2:
        st.markdown("### ⚡ Areas to Improve")
        for i in report.get("improvements", []):
            st.markdown(f"⚡ {i}")
    
    st.markdown("---")
    
    # Summary & Next steps
    st.markdown("### 📝 Overall Assessment")
    st.info(report.get("summary", ""))
    
    st.markdown("### 🚀 Next Steps")
    for step in report.get("next_steps", []):
        st.markdown(f"→ {step}")
    
    st.markdown("---")
    
    # Per-question score timeline
    if st.session_state.scores:
        st.markdown("### 📈 Your Score Timeline")
        score_data = {f"Q{i+1}": s for i, s in enumerate(st.session_state.scores)}
        st.bar_chart(score_data)
    
    # Retry button
    if st.button("🔄 Start New Interview", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
