import time
import random
import re
from google import genai
from google.genai import types
import config
import prompts

client = genai.Client(api_key=config.GEMINI_API_KEY)


def call_gemini_chat(system_prompt, user_prompt, history=None):
    """
    Simulates a chat interaction using the google-genai SDK.
    Includes Exponential Backoff to handle Free Tier Rate Limits (429 errors).
    """
    sdk_history = []
    if history:
        for msg in history:
            sdk_history.append(
                types.Content(
                    role="user" if msg['role'] == 'user' else 'model',
                    parts=[types.Part(text=msg['content'])]
                )
            )

    max_retries = 5
    base_delay = 2

    for i in range(max_retries):
        try:
            response = client.models.generate_content(
                model=config.GEMINI_MODEL_NAME,
                contents=sdk_history + [types.Content(role="user", parts=[types.Part(text=user_prompt)])],
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                )
            )

            if response.text:
                return response.text
            return "Error: Empty response from the timeline."

        except Exception as e:
            err_msg = str(e).lower()
            is_rate_limit = "429" in err_msg or "resource_exhausted" in err_msg or "exhausted" in err_msg

            if is_rate_limit and i < max_retries - 1:
                wait_time = (base_delay ** (i + 1)) + random.uniform(0, 1)
                time.sleep(wait_time)
                continue

            if i == max_retries - 1:
                return f"Error: {str(e)}"

            time.sleep(1)

    return "Error: Lost connection to the timeline."


def clean_markdown(text):
    """Removes common markdown headers that confuse the parser."""
    return re.sub(r'^#+.*$', '', text, flags=re.MULTILINE).strip()


def generate_initial_scenarios(data, history):
    system = prompts.SCENARIO_PROMPT_TEMPLATE.format(pessimism=data['pessimism'])
    user_input = f"User context: {data['about']}\nPurpose: {data['goal']}\nOriginal Plan: {data['plan']}"
    if data.get('wrong'):
        user_input += f"\nWhat I think goes wrong: {data['wrong']}"

    raw = call_gemini_chat(system, user_input, history)
    if raw.startswith("Error:"):
        return {"error": "API Error", "raw": raw}

    try:
        parts = raw.split('---')
        # Part 1: Problems
        problems_raw = clean_markdown(parts[0])
        problems = []
        for p in problems_raw.split('##'):
            if '|' in p:
                bits = p.split('|')
                problems.append({"title": bits[0].strip(), "desc": bits[1].strip(), "liked": None, "dislikes": None})

        # Part 2: Scenarios
        scenarios_raw = clean_markdown(parts[1])
        scenarios = []
        for s in scenarios_raw.split('##'):
            if '|' in s:
                # Robust parsing: try splitting by pipe first
                bits = [b.strip() for b in s.split('|')]
                if len(bits) >= 5:
                    scenarios.append({"title": bits[0], "desc": bits[1], "options": bits[2:5]})
                else:
                    # Fallback for when the model uses pipes for title/desc but lists for options
                    title = bits[0]
                    desc = bits[1]
                    # Find lines starting with "Option" or "1.", "2." etc
                    options = re.findall(r'(?:Option\s*\d+:|^\d+[\.\)])\s*(.*)', s, re.MULTILINE)
                    if len(options) >= 3:
                        scenarios.append({"title": title, "desc": desc, "options": options[:3]})

        return {"problems": problems, "scenarios": scenarios, "raw_response": raw}
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}", "raw": raw}


def generate_dashboard(data, maze_results, history):
    system = prompts.DASHBOARD_PROMPT_TEMPLATE.format(user_info=data['about'], plan=data['plan'])
    prompt = f"Decisions made in the Maze: {maze_results}\nOriginal Plan: {data['plan']}"

    raw = call_gemini_chat(system, prompt, history)
    if raw.startswith("Error:"):
        return {"error": "API Error", "raw": raw}

    try:
        parts = raw.split('---')
        # Check if model skipped a separator
        if len(parts) < 3:
            # Attempt to separate based on known headers if missing '---'
            revised_plan_search = re.split(r'Revised Plan|Final Plan', raw, flags=re.IGNORECASE)
            if len(revised_plan_search) > 1:
                top_part = clean_markdown(revised_plan_search[0])
                plan_part = revised_plan_search[1].strip()
                # Split top part into Problems/Improvements if possible
                sub_parts = top_part.split('##')
                return {
                    "problems": [],
                    "improvements": [{"title": i.split('|')[0].strip(), "desc": i.split('|')[1].strip()} for i in
                                     sub_parts if '|' in i],
                    "revised_plan": plan_part,
                    "raw_response": raw
                }
            raise ValueError(f"Expected 3 sections separated by '---', found {len(parts)}")

        problems = [{"title": p.split('|')[0].strip(), "desc": p.split('|')[1].strip(), "liked": None, "disliked": None}
                    for p in clean_markdown(parts[0]).split('##') if '|' in p]
        imps = [{"title": i.split('|')[0].strip(), "desc": i.split('|')[1].strip(), "liked": None, "disliked": None}
                for i in clean_markdown(parts[1]).split('##') if '|' in i]
        return {"problems": problems, "improvements": imps, "revised_plan": parts[2].strip(), "raw_response": raw}
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}", "raw": raw}


def refine_analysis(data, feedback_text, binary_feedback, history):
    system = prompts.FEEDBACK_PROMPT_TEMPLATE.format(user_info=data['about'], plan=data['plan'])
    prompt = f"Refine plan based on: {feedback_text}\nLikes: {binary_feedback}"

    raw = call_gemini_chat(system, prompt, history)
    if raw.startswith("Error:"):
        return {"error": "API Error", "raw": raw}

    try:
        parts = raw.split('---')
        if len(parts) < 3:
            return {"error": "Model response missing sections", "raw": raw}

        problems = [{"title": p.split('|')[0].strip(), "desc": p.split('|')[1].strip(), "liked": None, "disliked": None}
                    for p in clean_markdown(parts[0]).split('##') if '|' in p]
        imps = [{"title": i.split('|')[0].strip(), "desc": i.split('|')[1].strip(), "liked": None, "disliked": None}
                for i in clean_markdown(parts[1]).split('##') if '|' in i]
        return {"problems": problems, "improvements": imps, "revised_plan": parts[2].strip(), "raw_response": raw}
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}", "raw": raw}


def generate_followup(revised_plan, user_info, history):
    system = prompts.FOLLOWUP_PROMPT_TEMPLATE.format(user_info=user_info)
    prompt = f"Final Plan: {revised_plan}"

    raw = call_gemini_chat(system, prompt, history)
    if raw.startswith("Error:"):
        return {"error": "API Error", "raw": raw}

    try:
        parts = raw.split('---')
        tasks_raw = clean_markdown(parts[0])
        tasks = [
            {"title": t.split('|')[0].strip(), "time": t.split('|')[1].strip(), "instruction": t.split('|')[2].strip()}
            for t in tasks_raw.split('##') if '|' in t]
        return {"tasks": tasks, "advice": parts[1].strip(), "raw_response": raw}
    except Exception as e:
        return {"error": f"Parsing failed: {str(e)}", "raw": raw}