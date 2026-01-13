import os
import time
import requests
from config import GEMINI_API_KEY

MODEL_NAME = "gemini-2.5-flash-preview-09-2025"


def call_gemini(system_prompt, user_prompt):
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
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            time.sleep(2 ** i)
    return "Error: Timeline communication lost."


def generate_initial_scenarios(data):
    """
    Implements: Problem and scenario prompt
    """
    system_prompt = f"""You are a time traveler from a failed timeline in a real human world. Your job is to report all the unexpected events that happened that interfered with the plan I had made. Your level of pessimism is {data['pessimism']}. The unexpected events should range from day-to-day hiccups to catastrophic failures based on this level. 

    Task 1: The Problems - Think of all the problems that occurred in the failed timeline. Create a list of these problems where each entry has a title and a short one-sentence description. 
    Format: Title | Description. Separator: Separate each problem using ##
    
    Task 2: The Scenario Maze - Choose 3-5 unexpected events from the failed timeline. For each event, provide 3 distinct options for what I could have done to prepare for it. Each option must include 3 scores (ranging between 1-10): Stress level, Difference from original plan, and Feasibility.
    Scoring rubrics:
    Stressfulness: 1/10 -> Minor config change. 10/10 -> All-hands emergency/burnout.
    Difference from plan: 1/10 -> Virtually identical. 10/10 -> Total pivot.
    Feasibility: 1/10 -> Impossible/high cost. 10/10 -> Easy/immediate.
    
    Format: Event Title | Event Description | Option 1 [Stress: X, Deviation: Y, Feasibility: Z] | Option 2 [Stress: X, Deviation: Y, Feasibility: Z] | Option 3 [Stress: X, Deviation: Y, Feasibility: Z].
    Separator: Separate each scenario using ##
    
    Constraint: Do not use the |, ##, or --- symbols anywhere inside your descriptions.
    Separate Task 1 and Task 2 using ---"""

    user_prompt = f"""User Information: {data['about']}
    Purpose: {data['goal']}
    Plan: {data['plan']}
    Self-reflection: {data['wrong']}"""

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
        return {"error": "Parsing error", "raw": raw}


def generate_dashboard(data, maze_results):
    """
    Implements: Output dashboard prompt
    """
    system_prompt = f"""You are the time traveler from the failed timeline, but I am reporting to you from the "Revised Timeline." We have successfully used your reports to prepare for the obstacles that occurred during the Scenario Maze. 
    Task 1: The Problems – Refine the list of problems identified during the first stage.
    Task 3: The Improvement Guidelines – Based on the preparation decisions I made during the Scenario Maze, provide a list of strategic guidelines to improve the plan. 
    Format: title | description. Separator: separate each guideline using ##
    Task 4: The Revised Plan – Provide a detailed version of the improved plan. 
    Separate Task 1, Task 3, and Task 4 using ---"""

    user_prompt = f"""Original Plan: {data['plan']}
    Decisions made during Maze: {maze_results}
    User Context: {data['about']}"""

    raw = call_gemini(system_prompt, user_prompt)
    try:
        parts = raw.split('---')
        problems = [{"title": p.split('|')[0].strip(), "desc": p.split('|')[1].strip(), "liked": None}
                    for p in parts[0].strip().split('##') if '|' in p]
        imps = [{"title": i.split('|')[0].strip(), "desc": i.split('|')[1].strip(), "liked": None}
                for i in parts[1].strip().split('##') if '|' in i]
        return {"problems": problems, "improvements": imps, "revised_plan": parts[2].strip()}
    except:
        return {"error": "Dashboard parsing error", "raw": raw}


def refine_with_feedback(data, maze_results, feedback_text, binary_feedback):
    """
    Implements: Feedback prompt
    """
    system_prompt = f"""You are the time traveler from the failed timeline. We are refining the Revised Timeline based on specific feedback.
    Include binary feedback: {binary_feedback}
    Strict output format:
    The problems (task 1) – Format: Title | Description. Separator: ##
    The improvement guidelines (task 3) – Format: title | description. Separator: ##
    The revised plan (task 4) – Format: A detailed version of the improved plan.
    Separate tasks using ---"""

    user_prompt = f"Feedback: {feedback_text}\nContext: {data['about']}\nMaze: {maze_results}"
    raw = call_gemini(system_prompt, user_prompt)
    # Parsing logic same as generate_dashboard
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
    Implements: Follow up dashboard prompt
    """
    system_prompt = f"""You are the time traveler from the failed timeline. We have successfully constructed a resilient, revised plan.
    Task 5: The Task Checklist – Break down the plan into specific, bite-sized actionable tasks.
    Format: Task title | Estimated Duration/Time | Specific Instruction. Separator: separate each task using ##
    Task 6: The Time Traveler’s Advice – Provide a 2-3 sentence encouraging message.
    Constraint: Do not use |, ##, or --- inside descriptions.
    Separate using ---"""

    user_prompt = f"Plan: {revised_plan}\nUser Info: {user_info}"
    raw = call_gemini(system_prompt, user_prompt)
    try:
        parts = raw.split('---')
        tasks = [
            {"title": t.split('|')[0].strip(), "time": t.split('|')[1].strip(), "instruction": t.split('|')[2].strip()}
            for t in parts[0].strip().split('##') if '|' in t]
        return {"tasks": tasks, "advice": parts[1].strip()}
    except:
        return None