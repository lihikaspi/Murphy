from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import llm_logic
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


def add_to_history(role, content):
    """Utility to manage the chat history within the Flask session."""
    if 'chat_history' not in session:
        session['chat_history'] = []
    session['chat_history'].append({"role": role, "content": content})
    session.modified = True


@app.route('/')
def index():
    return render_template('input.html', data=session.get('user_input', {}))


@app.route('/process_input', methods=['POST'])
def process_input():
    about = request.form.get('about', '').strip()
    goal = request.form.get('goal', '').strip()
    plan = request.form.get('plan', '').strip()
    wrong = request.form.get('wrong', '').strip()
    pessimism = request.form.get('pessimism', 'Realistic') # Default to Realistic

    # If any required field is empty after stripping whitespace, redirect back to index
    if not all([about, goal, plan]):
        return redirect(url_for('index'))

    session['chat_history'] = []  # Reset history for a new plan sequence
    session['user_input'] = {
        'about': about,
        'goal': goal,
        'plan': plan,
        'wrong': wrong,
        'pessimism': pessimism
    }

    # Proceed with scenario generation
    res = llm_logic.generate_initial_scenarios(session['user_input'], session['chat_history'])

    if "error" in res:
        return f"Simulation Error: {res.get('raw')}"

    # Record interaction for context
    add_to_history("user", f"Here is my plan for {session['user_input']['goal']}")
    add_to_history("model", res['raw_response'])

    session['problems'] = res['problems']
    session['scenarios'] = res['scenarios']
    session['maze_idx'] = 0
    session['maze_answers'] = []
    session['versions'] = [] # Lock "Revised Strategy" until maze is finished

    return redirect(url_for('maze'))


@app.route('/maze')
def maze():
    idx = session.get('maze_idx', 0)
    scenarios = session.get('scenarios', [])
    if idx >= len(scenarios):
        return redirect(url_for('finalize_timeline'))
    return render_template('choice.html', scenario=scenarios[idx], index=idx + 1, total=len(scenarios))


@app.route('/process_maze', methods=['POST'])
def process_maze():
    ans = request.form.get('choice')
    if ans == "Other":
        ans = request.form.get('other_text')

    # Capture the title of the scenario the user just answered
    idx = session.get('maze_idx', 0)
    scenarios = session.get('scenarios', [])
    title = scenarios[idx]['title'] if idx < len(scenarios) else "Obstacle"

    # Store as a dict to show in timeline later
    session['maze_answers'].append({'title': title, 'answer': ans})
    session['maze_idx'] += 1
    session.modified = True
    return redirect(url_for('maze'))


@app.route('/finalize_timeline')
def finalize_timeline():
    res = llm_logic.generate_dashboard(session['user_input'], session['maze_answers'], session['chat_history'])

    add_to_history("user", f"I chose these solutions for the maze: {session['maze_answers']}")
    add_to_history("model", res['raw_response'])

    version = {
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "problems": session['problems'],
        "improvements": res['improvements'],
        "revised_plan": res['revised_plan'],
        "notes": "Initial analysis generated."
    }
    session['versions'] = [version]
    session['current_v_idx'] = 0
    session.modified = True
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    if not session.get('versions'):
        return redirect(url_for('index'))

    v_idx = session.get('current_v_idx', 0)
    return render_template('plan.html',
                           current=session['versions'][v_idx],
                           versions=session['versions'],
                           user_input=session['user_input'],
                           maze_choices=session['maze_answers'])


@app.route('/refine', methods=['POST'])
def refine():
    feedback = request.form.get('feedback', '').strip()

    # Requirement 1 & 2: Update session pessimism immediately
    # This ensures the top label and the AI context are updated
    new_pessimism = request.form.get('pessimism')
    if new_pessimism:
        session['user_input']['pessimism'] = new_pessimism
        session.modified = True

    # Requirement 3: Get the data from the CURRENTLY SELECTED version
    v_idx = session.get('current_v_idx', 0)
    # Ensure index is valid
    if v_idx >= len(session['versions']):
        v_idx = len(session['versions']) - 1

    base_version = session['versions'][v_idx]

    # Check for binary feedback on the selected version
    has_liked_probs = any(p.get('liked') is not None for p in base_version['problems'])
    has_liked_imps = any(i.get('liked') is not None for i in base_version['improvements'])

    if not feedback and not (has_liked_probs or has_liked_imps):
        return redirect(url_for('dashboard'))

    binary = {
        "liked_probs": [p['title'] for p in base_version['problems'] if p.get('liked')],
        "liked_imps": [i['title'] for i in base_version['improvements'] if i.get('liked')],
        "disliked_probs": [p['title'] for p in base_version['problems'] if p.get('disliked')],
        "disliked_imps": [i['title'] for i in base_version['improvements'] if i.get('disliked')]
    }

    # Pass the revised plan from the SELECTED version as the starting point
    # We modify the prompt call slightly to use base_version['revised_plan']
    res = llm_logic.refine_analysis(
        session['user_input'],
        feedback,
        binary,
        session['chat_history'],
        base_plan_override=base_version['revised_plan']  # Pass selected version context
    )

    if res:
        add_to_history("user", f"Refining version {v_idx + 1}. Feedback: {feedback}")
        add_to_history("model", res['raw_response'])

        note_text = f"Refined: {feedback[:40]}..." if feedback else "binary feedback given"

        new_version = {
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "problems": res['problems'],
            "improvements": res['improvements'],
            "revised_plan": res['revised_plan'],
            "notes": note_text
        }

        # Append as a new version
        session['versions'].append(new_version)
        # Set the new version as the active one
        session['current_v_idx'] = len(session['versions']) - 1
        session.modified = True

    return redirect(url_for('dashboard'))


@app.route('/set_version/<int:idx>')
def set_version(idx):
    session['current_v_idx'] = idx
    return redirect(url_for('dashboard'))


@app.route('/feedback_binary', methods=['POST'])
def feedback_binary():
    data = request.json
    v_idx = session.get('current_v_idx', 0)
    cat = 'problems' if data['type'] == 'problem' else 'improvements'
    session['versions'][v_idx][cat][data['idx']]['liked'] = data['liked']
    session.modified = True
    return {"status": "ok"}


@app.route('/followup')
def followup():
    if not session.get('versions'):
        return redirect(url_for('index'))

    v_idx = session.get('current_v_idx', 0)
    current = session['versions'][v_idx]

    # Feature 2: Followup data is attached to the version upon first access
    if 'followup' not in current:
        res = llm_logic.generate_followup(current['revised_plan'], session['user_input']['about'],
                                          session['chat_history'])
        add_to_history("user", "Construct my execution plan.")
        add_to_history("model", res['raw_response'])
        current['followup'] = res
        session.modified = True

    return render_template('followup.html', data=current['followup'], plan=current['revised_plan'])


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=config.DEBUG, port=5000)