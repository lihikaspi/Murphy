import time
import random
import json
from google import genai
from google.genai import types
import config
import prompts
from pinecone import Pinecone

client = genai.Client(api_key=config.GEMINI_API_KEY)

pc = Pinecone(api_key=config.PINECONE_API_KEY)
index = pc.Index(config.PINECONE_INDEX)


def call_gemini_json(system_prompt, user_prompt, history=None):
    """
    Calls Gemini with a forced JSON response schema.
    Utilizes system_instruction for the persona and task,
    and contents for the specific case data.
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
                    response_mime_type="application/json",
                )
            )

            if response.text:
                return json.loads(response.text)
            return {"error": "Empty response"}

        except Exception as e:
            err_msg = str(e).lower()
            # Exponential backoff for rate limiting
            if ("429" in err_msg or "resource_exhausted" in err_msg) and i < max_retries - 1:
                time.sleep((base_delay ** (i + 1)) + random.uniform(0, 1))
                continue

            if i == max_retries - 1:
                return {"error": f"API/JSON Error: {str(e)}", "raw": getattr(response, 'text', str(e))}
            time.sleep(1)

    return {"error": "Connection lost"}


def generate_initial_scenarios(data, history):
    """
    Step 1: Generates 10 problems and 3 scenario maze obstacles.
    """
    username = data.get('username', '')
    past_lessons = retrieve_user_history(username, data.get('plan', ''))

    system = prompts.SCENARIO_PROMPT_TEMPLATE.format(
        pessimism=data.get('pessimism', 'Realistic'),
        user_history=past_lessons
    )

    user_input = (
        f"User Background: {data.get('about')}\n"
        f"Primary Goal: {data.get('goal')}\n"
        f"Original Plan: {data.get('plan')}"
    )
    if data.get('wrong'):
        user_input += f"\nSpecific Concerns/Worries: {data['wrong']}"

    result = call_gemini_json(system, user_input, history)

    if "error" in result:
        return result

    return {
        "problems": result.get("problems", []),
        "scenarios": result.get("scenarios", []),
        "raw_response": json.dumps(result)
    }


def generate_dashboard(data, maze_results, history):
    """
    Step 2: Analyzes the choices made in the maze and provides a revised plan.
    """
    system = prompts.DASHBOARD_PROMPT_TEMPLATE.format(
        user_info=data.get('about'),
        plan=data.get('plan')
    )

    # Passing the maze results through the user prompt as requested in the instructions
    user_prompt = f"Maze Choices and Outcomes: {maze_results}\nPlease analyze these decisions and provide the revised strategy."

    result = call_gemini_json(system, user_prompt, history)
    if "error" in result:
        return result

    return {
        "problems": result.get("problems", []),  # Residual risks
        "improvements": result.get("improvements", []),
        "revised_plan": result.get("revised_plan", ""),
        "raw_response": json.dumps(result)
    }


def refine_analysis(data, feedback_text, binary_feedback, history):
    """
    Step 3: Refines the revised plan based on user feedback (likes/dislikes).
    """
    system = prompts.FEEDBACK_PROMPT_TEMPLATE.format(
        user_info=data.get('about'),
        plan=data.get('plan')
    )

    user_prompt = (
        f"User Feedback Notes: {feedback_text}\n"
        f"Binary Feedback (Likes/Dislikes): {binary_feedback}\n"
        "Please generate the 'Ultimate Resilient Plan' incorporating this feedback."
    )

    result = call_gemini_json(system, user_prompt, history)
    if "error" in result:
        return result

    return {
        "problems": result.get("problems", []),
        "improvements": result.get("improvements", []),
        "revised_plan": result.get("revised_plan", ""),
        "raw_response": json.dumps(result)
    }


def generate_followup(revised_plan, user_info, history):
    """
    Step 4: Provides the final execution checklist and traveler's advice.
    """
    system = prompts.FOLLOWUP_PROMPT_TEMPLATE.format(user_info=user_info)

    user_prompt = f"Final Revised Plan for Checklist Generation: {revised_plan}"

    result = call_gemini_json(system, user_prompt, history)
    if "error" in result:
        return result

    return {
        "tasks": result.get("tasks", []),
        "advice": result.get("advice", ""),
        "raw_response": json.dumps(result)
    }


def get_embedding(text):
    """
    Retrieves the embedding for the given text using Gemini embeddings.
    """
    try:
        result = client.models.embed_content(
            model="models/text-embedding-004",
            contents=text
        )
        # Handle potential API response structure differences
        if hasattr(result, 'embeddings'):
            return result.embeddings[0].values
        return []
    except Exception as e:
        print(f"Embedding Error: {e}")
        return []


def retrieve_user_history(username, current_plan):
    """
    Searches only within the specific user's namespace for past lessons.
    """
    if not username:
        return ""

    vector = get_embedding(current_plan)
    if not vector:
        return ""

    try:
        results = index.query(
            vector=vector,
            top_k=3,
            include_metadata=True,
            namespace=f"user_{username}"
        )

        if not results['matches']:
            return ""

        # Format the past failures into a readable string for the LLM
        history_text = "\n".join([
            f"- In project '{match['metadata']['goal']}', you failed due to: {match['metadata']['failure_summary']}"
            for match in results['matches']
        ])
        return history_text
    except Exception as e:
        print(f"Pinecone Query Error: {e}")
        return ""


def save_user_lesson(username, goal, plan, failure_summary):
    """
    Saves the 'Lesson Learned' into the user's private namespace.
    """
    if not username:
        return

    vector = get_embedding(plan)
    if not vector:
        return

    # Create a unique ID for this memory
    record_id = f"lesson_{int(time.time())}"

    try:
        index.upsert(
            vectors=[
                (
                    record_id,
                    vector,
                    {
                        "goal": goal,
                        "failure_summary": failure_summary
                    }
                )
            ],
            namespace=f"user_{username}"
        )
        print(f"Lesson saved for {username}")
    except Exception as e:
        print(f"Pinecone Upsert Error: {e}")