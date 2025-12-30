import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# Initialize Flask App
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for the frontend


# --- Mock LLM Logic (Replace with actual Google GenAI calls) ---
# In a real deployment, you would import google.genai here and use your API key.

def mock_generate_scenario(plan_data):
    """
    Simulates the LLM analyzing the plan and finding a failure.
    """
    return {
        "title": "Catastrophic Dependency Failure",
        "description": f"Based on your plan to '{plan_data.get('plan', 'execute strategy')}', a critical 3rd-party API you rely on creates a breaking change 2 hours before launch.",
        "consequences": "Your system hangs indefinitely. User trust drops by 60% immediately.",
        "options": [
            "Quick-patch a mock response (High technical debt)",
            "Delay launch by 24 hours (PR nightmare)",
            "Manually process requests (High labor cost)",
            "Other"
        ]
    }


def mock_generate_dashboard(user_input, choice, custom_choice_text):
    """
    Simulates the LLM generating the post-mortem dashboard.
    """
    decision = custom_choice_text if choice == "Other" else choice

    return {
        "title": "Project Fortification Report",
        "revised_plan": f"REVISED STRATEGY:\n1. Implement circuit breakers for all 3rd party APIs.\n2. {user_input.get('plan', 'Original steps')} with added redundancy.\n3. Pre-drafted communication templates for downtimes.",
        "problems": f"CRITICAL RISKS:\n- Single point of failure identified in API integration.\n- decision to '{decision}' introduces new latency risks.\n- Lack of automated rollback procedures.",
        "improvements": "ACTION ITEMS:\n- Add Redis caching layer to survive API outages.\n- Implement 'Chaos Monkey' testing weekly.\n- Hire a DevRel to manage community expectations during outages.",
        "history": f"Decision Log:\n[Initial] User chose to: {decision}"
    }


def mock_refine_dashboard(current_dashboard, feedback):
    """
    Simulates refining the dashboard based on user feedback.
    """
    return {
        **current_dashboard,
        "improvements": f"{current_dashboard['improvements']}\n\n[Refinement based on '{feedback}']: \n- Added granular monitoring for specific API endpoints."
    }


# --- API Endpoints ---

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "active", "message": "Murphy Backend Online"})


@app.route('/api/generate_scenario', methods=['POST'])
def generate_scenario():
    data = request.json
    # Here you would call your actual LLM function
    scenario = mock_generate_scenario(data)
    return jsonify(scenario)


@app.route('/api/generate_dashboard', methods=['POST'])
def generate_dashboard():
    data = request.json
    user_input = data.get('user_input', {})
    choice = data.get('choice', '')
    custom_choice = data.get('custom_choice', '')

    dashboard = mock_generate_dashboard(user_input, choice, custom_choice)
    return jsonify(dashboard)


@app.route('/api/refine_dashboard', methods=['POST'])
def refine_dashboard():
    data = request.json
    current_dashboard = data.get('current_dashboard', {})
    feedback = data.get('feedback', '')

    updated_dashboard = mock_refine_dashboard(current_dashboard, feedback)
    return jsonify(updated_dashboard)


if __name__ == '__main__':
    print("Murphy Backend running on http://localhost:5000")
    app.run(debug=True, port=5000)