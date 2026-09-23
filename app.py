import streamlit as st
import pandas as pd
import random
import json
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="SecOps-Pro Exam Simulator", layout="wide", page_icon="🛡️")

@st.cache_data
def load_questions():
    try:
        with open("questions.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Error: 'questions.json' not found. Run 'python build_master_json.py' first.")
        return []

all_questions = load_questions()

if "mode" not in st.session_state:
    st.session_state.mode = "Menu"
if "session_questions" not in st.session_state:
    st.session_state.session_questions = []
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted_current" not in st.session_state:
    st.session_state.submitted_current = False

st.sidebar.title("🛡️ SecOps-Pro Simulator")
st.sidebar.caption("Palo Alto Networks Certified Security Operations Professional")

if st.sidebar.button("🏠 Return to Menu"):
    st.session_state.mode = "Menu"
    st.rerun()

st.sidebar.markdown("---")

# MENU MODE
if st.session_state.mode == "Menu":
    st.title("Palo Alto Networks SecOps-Pro Exam Simulator")
    st.write(f"Loaded **{len(all_questions)} verified questions** across all 5 blueprint domains.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("📚 Study Mode")
        st.write("Immediate feedback, explanations, distractor analysis, and blueprint mapping after every question.")
        if st.button("Start Study Mode", use_container_width=True):
            st.session_state.mode = "Study"
            st.session_state.session_questions = all_questions.copy()
            st.session_state.current_idx = 0
            st.session_state.user_answers = {}
            st.session_state.submitted_current = False
            st.rerun()

    with col2:
        st.subheader("📝 Exam Mode")
        st.write("Uninterrupted mock examination. Zero feedback until final scorecard generation.")
        exam_length = st.selectbox("Number of Questions:", [20, 40, 60, len(all_questions)], index=1)
        if st.button("Start Exam Mode", use_container_width=True):
            st.session_state.mode = "Exam"
            shuffled = all_questions.copy()
            random.shuffle(shuffled)
            st.session_state.session_questions = shuffled[:exam_length]
            st.session_state.current_idx = 0
            st.session_state.user_answers = {}
            st.session_state.submitted_current = False
            st.rerun()

    with col3:
        st.subheader("🎯 Adaptive Mode")
        st.write("Filters practice questions dynamically by specific domain focus.")
        domains = sorted(list(set([q["domain"] for q in all_questions])))
        selected_domain = st.selectbox("Focus Domain:", domains)
        if st.button("Start Adaptive Session", use_container_width=True):
            st.session_state.mode = "Adaptive"
            filtered = [q for q in all_questions if q["domain"] == selected_domain]
            st.session_state.session_questions = filtered
            st.session_state.current_idx = 0
            st.session_state.user_answers = {}
            st.session_state.submitted_current = False
            st.rerun()

# QUESTION ENGINE
elif st.session_state.mode in ["Study", "Exam", "Adaptive"]:
    q_list = st.session_state.session_questions
    idx = st.session_state.current_idx

    if idx >= len(q_list):
        st.session_state.mode = "Scorecard"
        st.rerun()

    q = q_list[idx]

    st.caption(f"Mode: **{st.session_state.mode} Mode** | Question {idx + 1} of {len(q_list)} | ID: {q['id']}")
    st.progress((idx) / len(q_list))

    st.markdown(f"### {q['stem']}")
    st.info(f"**Domain:** {q['domain']}  \n**Objective:** {q['objective']}")

    if q["is_multiselect"]:
        st.warning(f"⚠️ **Select {len(q['answer'])} options**")

    selected_options = []
    if q["is_multiselect"]:
        for letter, text in q["options"].items():
            if st.checkbox(f"**{letter}.** {text}", key=f"cb_{q['id']}_{letter}"):
                selected_options.append(letter)
    else:
        choice = st.radio(
            "Choose your answer:",
            options=list(q["options"].keys()),
            format_func=lambda x: f"{x}. {q['options'][x]}",
            index=None,
            key=f"radio_{q['id']}"
        )
        if choice:
            selected_options = [choice]

    st.markdown("---")
    col_sub, col_next = st.columns([1, 1])

    if st.session_state.mode in ["Study", "Adaptive"]:
        if not st.session_state.submitted_current:
            if col_sub.button("Submit Answer", type="primary", use_container_width=True):
                if not selected_options:
                    st.error("Please select an answer before submitting.")
                else:
                    st.session_state.user_answers[q["id"]] = selected_options
                    st.session_state.submitted_current = True
                    st.rerun()
        else:
            user_ans = set(st.session_state.user_answers.get(q["id"], []))
            correct_ans = set(q["answer"])

            if user_ans == correct_ans:
                st.success("✅ **CORRECT!**")
            else:
                st.error(f"❌ **INCORRECT.** Correct Answer: **{', '.join(q['answer'])}**")

            st.markdown("#### Official Technical Logic & Explanation:")
            st.write(q["explanation"])

            # Gemini AI Integration
            api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)
            if api_key:
                st.markdown("---")
                st.subheader("🤖 Ask Gemini AI Tutor")
                user_query = st.text_input("Have a follow-up question about this concept?", key=f"ai_q_{q['id']}")
                if st.button("Ask AI Tutor"):
                    try:
                        from google import genai
                        client = genai.Client(api_key=api_key)
                        prompt = f"Question: {q['stem']}\nAnswer: {', '.join(q['answer'])}\nExplanation: {q['explanation']}\nUser query: {user_query}"
                        with st.spinner("Asking Gemini..."):
                            response = client.models.generate_content(
                                model="gemini-3.6-flash",
                                contents=prompt
                            )
                            st.write(response.text)
                    except Exception as e:
                        st.error(f"Gemini API Error: {e}")

            if col_next.button("Next Question ➡️", type="primary", use_container_width=True):
                st.session_state.current_idx += 1
                st.session_state.submitted_current = False
                st.rerun()

    elif st.session_state.mode == "Exam":
        if col_sub.button("Record Answer & Next ➡️", type="primary", use_container_width=True):
            if not selected_options:
                st.error("Please select an answer before continuing.")
            else:
                st.session_state.user_answers[q["id"]] = selected_options
                st.session_state.current_idx += 1
                st.rerun()

# SCORECARD MODE
elif st.session_state.mode == "Scorecard":
    st.title("📊 Examination Performance Scorecard")

    q_list = st.session_state.session_questions
    user_ans_dict = st.session_state.user_answers

    total_attempted = len(user_ans_dict)
    correct_count = 0
    domain_stats = {}

    for q in q_list:
        d = q["domain"]
        if d not in domain_stats:
            domain_stats[d] = {"total": 0, "correct": 0}
        
        domain_stats[d]["total"] += 1
        u_ans = set(user_ans_dict.get(q["id"], []))
        c_ans = set(q["answer"])
        
        if u_ans == c_ans:
            correct_count += 1
            domain_stats[d]["correct"] += 1

    accuracy = (correct_count / total_attempted * 100) if total_attempted > 0 else 0

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Questions", total_attempted)
    col_m2.metric("Correct Answers", f"{correct_count} / {total_attempted}")
    col_m3.metric("Raw Accuracy", f"{accuracy:.1f}%")

    st.subheader("Blueprint Domain Breakdown")
    table_data = []
    for dom in sorted(domain_stats.keys()):
        stats = domain_stats[dom]
        dom_acc = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        table_data.append({
            "SecOps-Pro Blueprint Domain": dom,
            "Questions": stats["total"],
            "Correct": stats["correct"],
            "Accuracy": f"{dom_acc:.1f}%"
        })
    st.table(pd.DataFrame(table_data))

    st.subheader("Question-by-Question Review")
    for q in q_list:
        u_ans = user_ans_dict.get(q["id"], [])
        is_correct = set(u_ans) == set(q["answer"])
        status = "✅ Correct" if is_correct else "❌ Incorrect"

        with st.expander(f"{status} | {q['id']} - {q['stem'][:80]}..."):
            st.write(f"**Full Question:** {q['stem']}")
            st.write(f"**Your Answer:** {', '.join(u_ans) if u_ans else 'None'}")
            st.write(f"**Correct Answer:** {', '.join(q['answer'])}")
            st.write(f"**Explanation:** {q['explanation']}")

    if st.button("Return to Main Menu"):
        st.session_state.mode = "Menu"
        st.rerun()