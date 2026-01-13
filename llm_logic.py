import os
import time
import requests
import json
from config import GEMINI_API_KEY

MODEL_NAME = "gemini-2.5-flash-preview-09-2025"


def call_gemini(system_prompt, user_prompt):
    """
    Standard caller for the Gemini API using exponential backoff.
    """
    api_key = GEMINI_API_KEY
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }

    for i in range(5):
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            time.sleep(2 ** i)
    return "Error: Timeline communication lost. Please try again."


def generate_initial_scenarios(data):
    """
    Implements: Problem and scenario prompt (Task 1 & Task 2)
    """
    system_prompt = f"""You are a time traveler from a failed timeline in a real human world. Your job is to report all the unexpected events that happened that interfered with the plan I had made. Your level of pessimism is {data['pessimism']}. The unexpected events should range from day-to-day hiccups to catastrophic failures based on this level. 

    Task 1: The Problems - Think of all the problems that occurred in the failed timeline. Create a list of these problems where each entry has a title and a short one-sentence description. 
    Format: Title | Description. Separator: Separate each problem using ##
    
    Task 2: The Scenario Maze - Choose 3-5 unexpected events from the failed timeline. For each event, provide 3 distinct options for what I could have done to prepare for it. Each option must include 3 scores (ranging between 1-10): Stress level, Difference from original plan, and Feasibility.
    Scoring rubrics:
    Stressfulness: 1/10 -> Minor change. 10/10 -> All-hands emergency/burnout.
    Difference from plan: 1/10 -> Virtually identical. 10/10 -> Total pivot.
    Feasibility: 1/10 -> Practically impossible. 10/10 -> Easy/immediate.
    
    Strict output format for task 2 (the scenarios): Each event and its options must follow this exact structure: Event Title | Event Description | Option 1 Text [Stress: X, Deviation: Y, Feasibility: Z] | Option 2 Text [Stress: X, Deviation: Y, Feasibility: Z] | Option 3 Text [Stress: X, Deviation: Y, Feasibility: Z].
    Separator: Separate each full event block using ##
    Constraint: Do not use the |, ##, or --- symbols anywhere inside your descriptions or titles.
    Separate the Problems section (task 1) and the Event section (task 2) using ---"""

    user_prompt = f"User info: {data['about']}\nPurpose: {data['goal']}\nPlan: {data['plan']}\nConcerns: {data['wrong']}"

    raw = call_gemini(system_prompt, user_prompt)
    try:
        parts = raw.split('---')
        # Parse Task 1: Problems
        problems = []
        for p in parts[0].strip().split('##'):
            if '|' in p:
                title, desc = p.split('|', 1)
                problems.append({"title": title.strip(), "desc": desc.strip(), "liked": None})

        # Parse Task 2: Scenarios
        scenarios = []
        for s in parts[1].strip().split('##'):
            if '|' in s:
                bits = [b.strip() for b in s.split('|')]
                if len(bits) >= 5:
                    scenarios.append({
                        "title": bits[0],
                        "desc": bits[1],
                        "options": bits[2:5]
                    })
        return {"problems": problems, "scenarios": scenarios}
    except Exception as e:
        return {"error": str(e), "raw": raw}


def generate_dashboard_data(data, maze_results):
    """
    Implements: Output dashboard prompt (Task 3 & Task 4)
    """
    system_prompt = f"""Now that I have navigated the Scenario Maze and made my choices on how to prepare for the obstacles you warned me about, your final task is to report from the "Revised Timeline".
Task 3: General Improvements (Guidelines) – Based on the failure points you identified in task 1 and the decisions I made in the maze, provide strategic improvements. Create a list where each entry has a title and a short description.
Format: title | description. Separator: separate each guideline using ##
Task 4: The Revised Plan – Synthesize the original plan with the general improvements and the specific maze solutions I selected. Rewrite the original plan into a Revised Plan that is realistic and resilient.
Format: A detailed version of the improved plan.
Output constraint: Do not use the |, ##, or --- symbols anywhere inside your descriptions or plan text.
Separate the improvements section (task 3) and the revised plan section (task 4) using ---"""

    user_prompt = f"Original Plan: {data['plan']}\nMaze Decisions: {maze_results}\nUser Context: {data['about']}"

    raw = call_gemini(system_prompt, user_prompt)
    try:
        parts = raw.split('---')
        improvements = []
        for i in parts[0].strip().split('##'):
            if '|' in i:
                title, desc = i.split('|', 1)
                improvements.append({"title": title.strip(), "desc": desc.strip(), "liked": None})

        return {"improvements": improvements, "revised_plan": parts[1].strip()}
    except Exception as e:
        return {"error": str(e), "raw": raw}


def refine_analysis(data, maze_results, current_version, text_feedback):
    """
    Implements: Feedback prompt
    """
    binary_feedback = {
        "prob_likes": [p['title'] for p in current_version['problems'] if p.get('liked') == True],
        "prob_dis": [p['title'] for p in current_version['problems'] if p.get('liked') == False],
        "impr_likes": [i['title'] for i in current_version['improvements'] if i.get('liked') == True],
        "impr_dis": [i['title'] for i in current_version['improvements'] if i.get('liked') == False]
    }

    system_prompt = f"""You are still the time traveler from the failed timeline. We are refining the Revised Timeline.
User Info: {data['about']}
Maze Decisions: {maze_results}
These are the problems I like: {binary_feedback['prob_likes']}
These are the problems I dislike: {binary_feedback['prob_dis']}
These are the improvements I like: {binary_feedback['impr_likes']}
These are the improvements I dislike: {binary_feedback['impr_dis']}
User Notes: {text_feedback}

Your Instructions:
Regenerate Task 1 (Problems): Keep all items marked as "liked". Replace "disliked" with more relevant items based on notes.
Regenerate Task 3 (Improvements): Keep "liked" items. Replace "disliked" with strategic improvements addressing concerns.
Regenerate Task 4 (The Revised Plan): Rewrite to be even more resilient, incorporating "liked" improvements and addressing textual notes.

Strict output format:
Problems (Task 1) - Format: Title | Description. Separator: ##
Improvements (Task 3) - Format: title | description. Separator: ##
Revised Plan (Task 4) - Format: Detailed text.
Separate the sections using ---"""

    raw = call_gemini(system_prompt, text_feedback)
    try:
        parts = raw.split('---')
        problems = [{"title": p.split('|')[0].strip(), "desc": p.split('|')[1].strip(), "liked": None}
                    for p in parts[0].strip().split('##') if '|' in p]
        imps = [{"title": i.split('|')[0].strip(), "desc": i.split('|')[1].strip(), "liked": None}
                for i in parts[1].strip().split('##') if '|' in i]
        return {"problems": problems, "improvements": imps, "revised_plan": parts[2].strip()}
    except:
        return None


def generate_followup(revised_plan, user_info):
    """
    Implements: Follow up dashboard prompt (Task 5 & Task 6)
    """
    system_prompt = """You are the time traveler from the failed timeline. 
Task 5: The Task Checklist – Break down the revised plan into specific, bite-sized actionable tasks.
Format: Task title | Estimated Duration/Time | Specific Instruction. Separator: separate each task using ##
Task 6: The Time Traveler’s Advice – Provide a brief (2-3 sentence) encouraging message.
Separate Task 5 and Task 6 using ---"""

    user_prompt = f"Finalized Plan: {revised_plan}\nUser context: {user_info}"
    raw = call_gemini(system_prompt, user_prompt)
    try:
        parts = raw.split('---')
        tasks = []
        for t in parts[0].strip().split('##'):
            if '|' in t:
                bits = t.split('|')
                tasks.append({
                    "title": bits[0].strip(),
                    "duration": bits[1].strip() if len(bits) > 1 else "TBD",
                    "instruction": bits[2].strip() if len(bits) > 2 else ""
                })
        return {"tasks": tasks, "advice": parts[1].strip()}
    except:
        return None