from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
from datetime import datetime
import llm_logic
import config
import db_logic

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
Session(app)


@app.context_processor
def inject_users():
    """Injects the user list into all templates for the sidebar."""
    return dict(all_users=db_logic.get_all_users())


def add_to_history(role, content):
    if 'chat_history' not in session:
        session['chat_history'] = []
    session['chat_history'].append({"role": role, "content": content})
    session.modified = True


@app.route('/')
def index():
    return render_template('input.html', data=session.get('user_input', {}))


@app.route('/add_user', methods=['POST'])
def add_new_user():
    """Handles adding a new user via the sidebar popup."""
    username = request.form.get('username')
    about = request.form.get('about')
    if username and about:
        new_user = db_logic.add_user(username, about)
        return redirect(url_for('switch_user', user_id=new_user['id']))
    return redirect(url_for('index'))


@app.route('/switch_user/<int:user_id>')
def switch_user(user_id):
    """Clears the session and starts a blank state for the selected user."""
    session.clear()
    user_data = db_logic.supabase.table("users").select("*").eq("id", user_id).single().execute()
    if user_data.data:
        session['db_user_id'] = user_data.data['id']
        session['user_input'] = {
            'username': user_data.data['username'],
            'about': user_data.data['about']
        }
    return redirect(url_for('index'))


@app.route('/process_input', methods=['POST'])
def process_input():
    username = request.form.get('username', '').strip()
    about = request.form.get('about', '').strip()
    goal = request.form.get('goal', '').strip()
    plan = request.form.get('plan', '').strip()
    wrong = request.form.get('wrong', '').strip()
    pessimism = request.form.get('pessimism', 'Realistic')

    if not all([username, about, goal, plan]):
        return redirect(url_for('index'))

    # Sync user background to DB
    db_user_id = db_logic.sync_user(username, about)
    session['db_user_id'] = db_user_id

    session['chat_history'] = []
    session['user_input'] = {
        'username': username,
        'about': about,
        'goal': goal,
        'plan': plan,
        'wrong': wrong,
        'pessimism': pessimism
    }

    res = llm_logic.generate_initial_scenarios(session['user_input'], session['chat_history'])
    if "error" in res:
        return f"Simulation Error: {res.get('raw')}"

    add_to_history("user", f"Here is my plan for {session['user_input']['goal']}")
    add_to_history("model", f"Generated 10 failures and {len(res['scenarios'])} scenarios.")

    session['problems'] = res['problems']
    session['scenarios'] = res['scenarios']
    session['maze_idx'] = 0
    session['maze_answers'] = []
    session['versions'] = []

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

    idx = session.get('maze_idx', 0)
    scenarios = session.get('scenarios', [])
    title = scenarios[idx]['title'] if idx < len(scenarios) else "Obstacle"

    session['maze_answers'].append({'title': title, 'answer': ans})
    session['maze_idx'] += 1
    session.modified = True
    return redirect(url_for('maze'))


@app.route('/finalize_timeline')
def finalize_timeline():
    res = llm_logic.generate_dashboard(session['user_input'], session['maze_answers'], session['chat_history'])
    add_to_history("user", f"I chose these solutions for the maze: {session['maze_answers']}")
    add_to_history("model", res.get('revised_plan', 'Plan revised.'))

    version = {
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "problems": session.get('problems', []),
        "improvements": res.get('improvements', []),
        "revised_plan": res.get('revised_plan', ''),
        "notes": "Initial analysis generated."
    }
    session['versions'] = [version]
    session['current_v_idx'] = 0

    # Save initial plan to Database
    plan_id = db_logic.create_plan_entry(
        user_id=session['db_user_id'],
        user_input=session['user_input'],
        maze_results=session['maze_answers'],
        versions=session['versions'],
        chat_history=session['chat_history']
    )
    session['plan_db_id'] = plan_id

    session.pop('scenarios', None)
    session.pop('problems', None)
    session.modified = True
    return redirect(url_for('dashboard'))


@app.route('/refine', methods=['POST'])
def refine():
    feedback = request.form.get('feedback', '').strip()
    new_pessimism = request.form.get('pessimism')
    if new_pessimism:
        session['user_input']['pessimism'] = new_pessimism

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
        "liked_problems": [p['desc'] for p in base_version['problems'] if p.get('liked')],
        "disliked_problems": [p['desc'] for p in base_version['problems'] if p.get('disliked')],
        "liked_improvements": [i['desc'] for i in base_version['improvements'] if i.get('liked')],
        "disliked_improvements": [i['desc'] for i in base_version['improvements'] if i.get('disliked')]
    }

    res = llm_logic.refine_analysis(session['user_input'], feedback, binary, session['chat_history'])

    if res:
        add_to_history("user", f"Refining version {v_idx + 1}. Feedback: {feedback}")
        add_to_history("model", res.get('revised_plan', 'Plan updated.'))

        new_version = {
            "timestamp": datetime.now().strftime("%I:%M %p"),
            "problems": res['problems'],
            "improvements": res['improvements'],
            "revised_plan": res['revised_plan'],
            "notes": f"{feedback[:50]}..." if feedback else "binary feedback given"
        }
        session['versions'].append(new_version)
        session['current_v_idx'] = len(session['versions']) - 1

        # Sync update to DB
        db_logic.update_existing_plan(
            plan_id=session['plan_db_id'],
            versions=session['versions'],
            chat_history=session['chat_history'],
            pessimism=session['user_input']['pessimism']
        )
    return redirect(url_for('dashboard'))


@app.route('/feedback_binary', methods=['POST'])
def feedback_binary():
    data = request.json
    v_idx = session.get('current_v_idx', 0)
    cat = 'problems' if data['type'] == 'problem' else 'improvements'
    session['versions'][v_idx][cat][data['idx']]['liked'] = data['liked']
    session.modified = True

    # Sync binary feedback to DB
    db_logic.update_existing_plan(
        plan_id=session['plan_db_id'],
        versions=session['versions'],
        chat_history=session['chat_history']
    )
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
        add_to_history("model", "Execution plan and advice generated.")
        current['followup'] = res
        session.modified = True

    return render_template('followup.html', data=current['followup'], plan=current['revised_plan'])


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=config.DEBUG, port=5000)