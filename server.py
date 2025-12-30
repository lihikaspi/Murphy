import os
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)


# --- MOCK LOGIC: Multi-Stage Scenarios ---
def mock_generate_scenarios(plan_data):
    """Generates a list of 3 distinct failure scenarios."""
    base_plan = plan_data.get('plan', '')[:20]
    return [
        {
            "id": 1,
            "title": "The Dependency Trap",
            "description": f"Your plan relies heavily on a specific API/Tool mentioned in '{base_plan}...'. Two days before launch, they change their pricing model, making your unit economics negative.",
            "consequences": "Instant insolvency if not mitigated within 48 hours.",
            "options": ["Absorb the cost temporarily", "Emergency rewrite (Delay 2 weeks)", "Pass cost to users"]
        },
        {
            "id": 2,
            "title": "The Silent Bug",
            "description": "A race condition in your database that wasn't caught in testing corrupts 5% of user data during the initial onboarding surge.",
            "consequences": "Permanent loss of trust from early adopters.",
            "options": ["Rollback and restore (24hr downtime)", "Manual data patching (High labor)",
                        "Ignore and fix forward"]
        },
        {
            "id": 3,
            "title": "Legal Ambush",
            "description": "A competitor issues a cease-and-desist letter claiming your core feature infringes on a vague patent they hold.",
            "consequences": "Potential lawsuit draining 100% of runway.",
            "options": ["Comply and remove feature", "Fight it in court", "Pivot product direction"]
        }
    ]


def mock_generate_dashboard(user_input, all_choices):
    """Generates the final dashboard data."""
    return {
        "title": "Strategic Fortification Dashboard",
        "revised_plan": f"REVISED STRATEGY:\n1. Abstract all external dependencies behind a service interface.\n2. {user_input.get('plan', 'Original steps')} with added redundancy.\n3. Maintain a 3-month runway cash reserve.\n4. Implement chaotic testing for database.",
        "problems": "CRITICAL WEAKNESSES:\n- Heavy reliance on external pricing models.\n- Single point of failure in database architecture.\n- Lack of legal contingency for IP disputes.\n- No budget allocation for customer acquisition cost spikes.",
        "improvements": "ACTION ITEMS:\n- Audit all 3rd party SLAs.\n- Implement 'Adapter Pattern' in codebase.\n- Establish legal defense fund.\n- Diversify API vendors.",
        "feedback_history": []  # For the refinement log
    }


def mock_refine_dashboard(current_dashboard, feedback, pessimism):
    """Updates dashboard based on feedback."""
    # Add to log
    log_entry = {
        "time": datetime.now().strftime('%H:%M'),
        "pessimism": pessimism,
        "text": feedback
    }
    current_dashboard["feedback_history"].insert(0, log_entry)

    # Mock update to text
    current_dashboard["improvements"] += f"\n- [New] Address feedback: {feedback}"
    return current_dashboard


# --- ROUTES ---

@app.route('/')
def index():
    return render_template('input.html', data=session.get('user_input', {}))


@app.route('/process_input', methods=['POST'])
def process_input():
    # 1. Save User Input
    session['user_input'] = {
        'about': request.form.get('about'),
        'goal': request.form.get('goal'),
        'plan': request.form.get('plan'),
        'wrong': request.form.get('wrong'),
        'pessimism': request.form.get('pessimism')
    }

    # 2. Generate Scenarios & Reset State
    session['scenarios'] = mock_generate_scenarios(session['user_input'])
    session['current_index'] = 0  # Start at first scenario
    session['user_choices'] = []  # Clear previous choices

    return redirect(url_for('choice'))


@app.route('/choice')
def choice():
    scenarios = session.get('scenarios', [])
    index = session.get('current_index', 0)

    # Check if simulation is done or valid
    if not scenarios or index >= len(scenarios):
        return redirect(url_for('dashboard'))

    current_scenario = scenarios[index]

    return render_template('choice.html',
                           scenario=current_scenario,
                           index=index + 1,
                           total=len(scenarios))


@app.route('/process_choice', methods=['POST'])
def process_choice():
    # 1. Capture Decision
    choice_val = request.form.get('contingency')
    custom_text = request.form.get('custom_text', '')
    decision = custom_text if choice_val == "Other" else choice_val

    scenarios = session.get('scenarios', [])
    index = session.get('current_index', 0)

    # 2. Record Decision
    current_record = {
        "scenario_title": scenarios[index]['title'],
        "scenario_icon": "siren" if index == 0 else ("bug" if index == 1 else "gavel"),  # Mock icon logic
        "decision": decision,
        "id": index + 1
    }

    choices = session.get('user_choices', [])
    choices.append(current_record)
    session['user_choices'] = choices

    # 3. Advance or Finish
    session['current_index'] = index + 1

    if session['current_index'] >= len(scenarios):
        # Generate final dashboard
        session['dashboard_data'] = mock_generate_dashboard(
            session.get('user_input', {}),
            session.get('user_choices', [])
        )
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('choice'))


@app.route('/dashboard')
def dashboard():
    data = session.get('dashboard_data')
    if not data: return redirect(url_for('index'))

    return render_template(
        'dashboard.html',
        dashboard=data,
        user_plan=session.get('user_input', {}).get('plan'),
        choices=session.get('user_choices', [])
    )


@app.route('/refine', methods=['POST'])
def refine():
    feedback = request.form.get('feedback')
    pessimism = request.form.get('pessimism')

    if feedback and session.get('dashboard_data'):
        data = session['dashboard_data']
        session['dashboard_data'] = mock_refine_dashboard(data, feedback, pessimism)
        session.modified = True

    return redirect(url_for('dashboard'))


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)