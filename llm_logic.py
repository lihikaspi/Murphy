import os
import time
import requests
import json

MODEL_NAME = "gemini-2.5-flash-preview-09-2025"


def call_gemini(system_prompt, user_prompt):
    api_key = ""  # Key provided by environment
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }

    for i in range(5):
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except:
            time.sleep(2 ** i)
    return "Error: Timeline communication lost."


def generate_scenarios(data):
    """Task 1: Problems & Task 2: Scenario Maze"""
    system_prompt = f"""You are a time traveler from a failed timeline. Pessimism: {data['pessimism']}.
Task 1: The Problems - Format: Title | Description. Separator: ##
Task 2: The Scenario Maze (3-5 events) - Format: Event Title | Event Description | Option 1 [Stress: X, Deviation: Y, Feasibility: Z] | Option 2 [Stress: X, Deviation: Y, Feasibility: Z] | Option 3 [Stress: X, Deviation: Y, Feasibility: Z].
Separator: ##
Split Tasks using ---"""

    user_prompt = f"User: {data['about']}\nGoal: {data['goal']}\nPlan: {data['plan']}\nConcerns: {data['wrong']}"
    raw = call_gemini(system_prompt, user_prompt)

    try:
        parts = raw.split('---')
        problems = [{"title": p.split('|')[0].strip(), "desc": p.split('|')[1].strip(), "liked": None}
                    for p in parts[0].strip().split('##') if '|' in p]

        scenarios = []
        for s in parts[1].strip().split('##'):
            if '|' in s:
                bits = [b.strip() for b in s.split('|')]
                if len(bits) >= 5:
                    scenarios.append({"title": bits[0], "desc": bits[1], "options": bits[2:5]})
        return {"problems": problems, "scenarios": scenarios}
    except:
        return None


def generate_refinement(data, maze_results, feedback_text=None, binary_feedback=None):
    """Task 3: Improvements & Task 4: Revised Plan"""
    system_prompt = """You are the Time Traveler.
Task 3: Improvements - Format: Title | Description. Separator: ##
Task 4: Revised Plan - Detailed rewrite.
Split Tasks using ---"""

    user_prompt = f"Original Plan: {data['plan']}\nMaze Choices: {maze_results}"
    if feedback_text:
        user_prompt += f"\nUser Feedback: {feedback_text}\nLiked/Disliked elements: {binary_feedback}"

    raw = call_gemini(system_prompt, user_prompt)

    try:
        parts = raw.split('---')
        imps = [{"title": i.split('|')[0].strip(), "desc": i.split('|')[1].strip(), "liked": None}
                for i in parts[0].strip().split('##') if '|' in i]
        return {"improvements": imps, "revised_plan": parts[1].strip()}
    except:
        return None


def generate_followup(plan, user_info):
    """Task 5: Tasks & Task 6: Advice"""
    system_prompt = "Task 5: Checklist (Title | Duration | Instruction ##). Task 6: Advice. Split using ---"
    raw = call_gemini(system_prompt, f"Plan: {plan}\nUser: {user_info}")

    try:
        parts = raw.split('---')
        tasks = [{"title": t.split('|')[0], "time": t.split('|')[1], "note": t.split('|')[2]}
                 for t in parts[0].strip().split('##') if '|' in t]
        return {"tasks": tasks, "advice": parts[1].strip()}
    except:
        return None