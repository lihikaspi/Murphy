import os
import time
import requests
import json
import config
import prompts

MODEL_NAME = "gemini-2.5-flash-preview-09-2025"


def call_gemini_chat(system_prompt, user_prompt, history=None):
    """
    Simulates a chat interaction by sending the session history alongside the new prompt.
    """
    api_key = config.GEMINI_API_KEY
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"

    # Initialize contents with history if available
    contents = []
    if history:
        for msg in history:
            contents.append({
                "role": "user" if msg['role'] == 'user' else 'model',
                "parts": [{"text": msg['content']}]
            })

    # Add current prompt
    contents.append({
        "role": "user",
        "parts": [{"text": user_prompt}]
    })

    payload = {
        "contents": contents,
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }

    for i in range(5):
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            text = response.json()['candidates'][0]['content']['parts'][0]['text']
            return text
        except Exception:
            time.sleep(2 ** i)
    return "Error: Lost connection to the timeline."


def get_rag_plans(data):
    # TODO: decide what should go into the RAG index
    pass


def generate_initial_scenarios(data, history):
    system = prompts.SCENARIO_PROMPT_TEMPLATE.format(pessimism=data['pessimism'])
    user_input = f"""
    User context: {data['about']}
    Purpose: {data['goal']}
    Original Plan: {data['plan']}
    """

    if data['wrong']:
        user_input += f"""\nWhat I think goes wrong: {data['wrong']}"""

    if get_rag_plans(data):
        # TODO: update text when RAG index is decided upon
        user_input += f"""\nSimilar plans: {get_rag_plans(data)}"""

    raw = call_gemini_chat(system, user_input, history)
    try:
        parts = raw.split('---')
        problems = [{"title": p.split('|')[0].strip(), "desc": p.split('|')[1].strip(), "liked": None, "dislikes": None}
                    for p in parts[0].strip().split('##') if '|' in p]

        scenarios = []
        for s in parts[1].strip().split('##'):
            if '|' in s:
                bits = [b.strip() for b in s.split('|')]
                if len(bits) >= 5:
                    scenarios.append({"title": bits[0], "desc": bits[1], "options": bits[2:5]})
        return {"problems": problems, "scenarios": scenarios, "raw_response": raw}
    except:
        return {"error": "Parsing failed", "raw": raw}


def generate_dashboard(data, maze_results, history):
    system = prompts.DASHBOARD_PROMPT_TEMPLATE.format(user_info=data['about'], plan=data['plan'])
    prompt = f"Decisions made in the Maze: {maze_results}\nOriginal Plan: {data['plan']}"

    raw = call_gemini_chat(system, prompt, history)
    try:
        parts = raw.split('---')
        problems = [{"title": p.split('|')[0].strip(), "desc": p.split('|')[1].strip(), "liked": None, "disliked": None}
                    for p in parts[0].strip().split('##') if '|' in p]
        imps = [{"title": i.split('|')[0].strip(), "desc": i.split('|')[1].strip(), "liked": None, "disliked": None}
                for i in parts[1].strip().split('##') if '|' in i]
        return {"problems": problems, "improvements": imps, "revised_plan": parts[2].strip(), "raw_response": raw}
    except:
        return None


def refine_analysis(data, feedback_text, binary_feedback, history):
    system = prompts.FEEDBACK_PROMPT_TEMPLATE.format(user_info=data['about'], plan=data['plan'])
    prompt = f"""
    These are the problems I like: {binary_feedback['liked_probs']}
    These are the problems I dislike: {binary_feedback['disliked_probs']}
    These are the improvements I like: {binary_feedback['liked_imps']}
    These are the improvements I dislike: {binary_feedback['disliked_imps']}
    I also have notes about the revised plan and the analysis of the original plan: {feedback_text} 
    """

    raw = call_gemini_chat(system, prompt, history)
    try:
        parts = raw.split('---')
        problems = [{"title": p.split('|')[0].strip(), "desc": p.split('|')[1].strip(), "liked": None, "disliked": None}
                    for p in parts[0].strip().split('##') if '|' in p]
        imps = [{"title": i.split('|')[0].strip(), "desc": i.split('|')[1].strip(), "liked": None, "disliked": None}
                for i in parts[1].strip().split('##') if '|' in i]
        return {"problems": problems, "improvements": imps, "revised_plan": parts[2].strip(), "raw_response": raw}
    except:
        return None


def generate_followup(revised_plan, user_info, history):
    system = prompts.FOLLOWUP_PROMPT_TEMPLATE.format(user_info=user_info)
    prompt = f"The finalized revised Plan: {revised_plan}"

    raw = call_gemini_chat(system, prompt, history)
    try:
        parts = raw.split('---')
        tasks = [
            {"title": t.split('|')[0].strip(), "time": t.split('|')[1].strip(), "instruction": t.split('|')[2].strip()}
            for t in parts[0].strip().split('##') if '|' in t]
        return {"tasks": tasks, "advice": parts[1].strip(), "raw_response": raw}
    except:
        return None