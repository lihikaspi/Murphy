import os
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import llm_logic

app = Flask(__name__)
app.secret_key = "murphy_secret_key_v2"  # Using standard key for session


@app.route('/')
def index():
    # Pre-fill data if user is editing
    return render_template('input.html', data=session.get('user_input', {}))


@app.route('/process_input', methods=['POST'])
def process_input():
    session['user_input'] = {
        'about': request.form.get('about'),
        'goal': request.form.get('goal'),
        'plan': request.form.get('plan'),
        'wrong': request.form.get('wrong'),
        'pessimism': request.form.get('pessimism')
    }

    # Generate failure scenarios
    result = llm_logic.generate_initial_scenarios(session['user_input'])
    if "error" in result:
        return f"Error communicating with the future: {result.get('raw')}"

    session['problems'] = result['problems']
    session['scenarios'] = result['scenarios']
    session['maze_index'] = 0
    session['maze_choices'] = []
    session['versions'] = []

    return redirect(url_for('maze'))


@app.route('/maze')
def maze():
    scenarios = session.get('scenarios', [])
    idx = session.get('maze_index', 0)

    if idx >= len(scenarios):
        return redirect(url_for('finalize_timeline'))

    return render_template('choice.html',
                           scenario=scenarios[idx],
                           index=idx + 1,
                           total=len(scenarios))


@app.route('/process_maze', methods=['POST'])
def process_maze():
    ans = request.form.get('choice')
    if ans == "Other":
        ans = request.form.get('other_text')

    session['maze_choices'].append(ans)
    session['maze_index'] += 1
    session.modified = True
    return redirect(url_for('maze'))


@app.route('/finalize_timeline')
def finalize_timeline():
    # Initial generation of improvements and revised plan
    res = llm_logic.generate_dashboard_data(session['user_input'], session['maze_choices'])

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
    versions = session.get('versions', [])
    if not versions:
        return redirect(url_for('index'))

    v_idx = session.get('current_v_idx', 0)
    return render_template('plan.html',
                           current=versions[v_idx],
                           versions=versions,
                           user_input=session['user_input'],
                           maze_choices=session['maze_choices'])


@app.route('/refine', methods=['POST'])
def refine():
    feedback = request.form.get('feedback')
    v_idx = session.get('current_v_idx', 0)
    current = session['versions'][v_idx]

    res = llm_logic.refine_analysis(session['user_input'], session['maze_choices'], current, feedback)

    if res:
        new_version = {
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "problems": res['problems'],
            "improvements": res['improvements'],
            "revised_plan": res['revised_plan'],
            "notes": f"Refined: {feedback[:40]}..."
        }
        session['versions'].append(new_version)
        session['current_v_idx'] = len(session['versions']) - 1
        session.modified = True

    return redirect(url_for('dashboard'))


@app.route('/feedback_binary', methods=['POST'])
def feedback_binary():
    # Update like/dislike state in the current version
    data = request.json
    v_idx = session.get('current_v_idx', 0)
    category = 'problems' if data['type'] == 'problem' else 'improvements'
    session['versions'][v_idx][category][data['idx']]['liked'] = data['liked']
    session.modified = True
    return {"status": "ok"}


@app.route('/set_version/<int:idx>')
def set_version(idx):
    session['current_v_idx'] = idx
    return redirect(url_for('dashboard'))


@app.route('/followup')
def followup():
    v_idx = session.get('current_v_idx', 0)
    current = session['versions'][v_idx]

    if 'followup' not in current:
        res = llm_logic.generate_followup(current['revised_plan'], session['user_input']['about'])
        current['followup'] = res
        session.modified = True

    return render_template('followup.html', data=current['followup'], plan=current['revised_plan'])


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, port=5000)