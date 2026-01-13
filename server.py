from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import llm_logic

app = Flask(__name__)
app.secret_key = "murphy_v2_secret"


@app.route('/')
def index():
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
    res = llm_logic.generate_scenarios(session['user_input'])
    session['problems'] = res['problems']
    session['scenarios'] = res['scenarios']
    session['current_maze_idx'] = 0
    session['maze_answers'] = []
    session['history'] = []
    return redirect(url_for('maze'))


@app.route('/maze')
def maze():
    idx = session.get('current_maze_idx', 0)
    scenarios = session.get('scenarios', [])
    if idx >= len(scenarios):
        return redirect(url_for('finalize_timeline'))
    return render_template('choice.html', scenario=scenarios[idx], index=idx + 1, total=len(scenarios))


@app.route('/process_maze', methods=['POST'])
def process_maze():
    ans = request.form.get('choice')
    if ans == "Other":
        ans = request.form.get('other_text')

    session['maze_answers'].append(ans)
    session['current_maze_idx'] += 1
    session.modified = True
    return redirect(url_for('maze'))


@app.route('/finalize_timeline')
def finalize_timeline():
    res = llm_logic.generate_refinement(session['user_input'], session['maze_answers'])

    new_version = {
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "problems": session['problems'],
        "improvements": res['improvements'],
        "revised_plan": res['revised_plan'],
        "notes": "Initial timeline generated."
    }

    if 'versions' not in session: session['versions'] = []
    session['versions'].append(new_version)
    session['current_v_idx'] = len(session['versions']) - 1
    session.modified = True
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
def dashboard():
    v_idx = session.get('current_v_idx', 0)
    return render_template('plan.html',
                           current=session['versions'][v_idx],
                           versions=session['versions'],
                           user_input=session['user_input'])


@app.route('/refine', methods=['POST'])
def refine():
    feedback = request.form.get('feedback')
    v_idx = session.get('current_v_idx', 0)
    current = session['versions'][v_idx]

    # Collect binary feedback state
    binary = {"liked_probs": [p['title'] for p in current['problems'] if p.get('liked')],
              "liked_imps": [i['title'] for i in current['improvements'] if i.get('liked')]}

    res = llm_logic.generate_refinement(session['user_input'], session['maze_answers'], feedback, binary)

    new_version = {
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "problems": current['problems'],  # Carry over current problems
        "improvements": res['improvements'],
        "revised_plan": res['revised_plan'],
        "notes": f"Refinement: {feedback[:50]}..."
    }
    session['versions'].append(new_version)
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
    target = 'problems' if data['type'] == 'problem' else 'improvements'
    session['versions'][v_idx][target][data['idx']]['liked'] = data['liked']
    session.modified = True
    return {"status": "ok"}


@app.route('/followup')
def followup():
    v_idx = session.get('current_v_idx', 0)
    current = session['versions'][v_idx]
    if 'followup' not in current:
        current['followup'] = llm_logic.generate_followup(current['revised_plan'], session['user_input']['about'])
        session.modified = True
    return render_template('followup.html', data=current['followup'], plan=current['revised_plan'])


if __name__ == '__main__':
    app.run(debug=True, port=5000)