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
def inject_global_vars():
    """Injects global variables into all templates."""
    user_plans = []

    current_user_id = session.get('db_user_id', -1)
    if current_user_id != -1 and 'user_input' in session:
        username = session['user_input'].get('username')
        if username:
            user_plans = db_logic.get_user_plans(username)

    return dict(
        all_users=db_logic.get_all_users(),
        has_versions=len(session.get('versions', [])) > 0,
        user_history=user_plans
    )


def add_to_history(role, content):
    if 'chat_history' not in session:
        session['chat_history'] = []
    session['chat_history'].append({"role": role, "content": content})
    session.modified = True


def perform_switch_user(user_id):
    old_id = session.get('db_user_id', -1)

    # Only clear everything if we are switching to a DIFFERENT person
    if user_id != old_id:
        session.clear()
        session['db_user_id'] = user_id

    # Refresh profile info (About/Username) from DB
    user_data = db_logic.supabase.table("users").select("*").eq("id", user_id).single().execute()
    if user_data.data:
        if 'user_input' not in session:
            session['user_input'] = {'pessimism': 'Realistic'}

        # Update profile info while keeping draft fields (goal/plan)
        session['user_input'].update({
            'username': user_data.data['username'],
            'about': user_data.data['about']
        })
        session['db_user_id'] = user_data.data['id']


@app.route('/')
def welcome():
    """
    Landing page: Renders the welcome view.
    Does NOT clear the session so that logo clicks preserve progress.
    """
    if 'db_user_id' not in session:
        session['db_user_id'] = -1
        session['user_input'] = {'pessimism': 'Realistic'}

    return render_template('welcome.html')


@app.route('/input')
def index():
    """Input page: Where the user submits their goal and plan."""
    # Prevent accessing input without a selected user
    if session.get('db_user_id', -1) == -1:
        return redirect(url_for('welcome'))

    return render_template('input.html', data=session.get('user_input', {}))


@app.route('/add_user', methods=['POST'])
def add_new_user():
    """Handles adding a new user and going straight to input."""
    username = request.form.get('username')
    about = request.form.get('about')
    if username and about:
        new_user = db_logic.add_user(username, about)
        perform_switch_user(new_user['id'])
        return redirect(url_for('index'))
    return redirect(url_for('welcome'))


@app.route('/switch_user', methods=['POST'])
def switch_user_route():
    """Handles 'Get Started' click: updates user and goes to input page."""
    user_id = int(request.form.get('user_id', -1))
    if user_id != -1:
        perform_switch_user(user_id)
    return redirect(url_for('index'))


@app.route('/change_user')
def change_user():
    """
    Explicitly clears the session and returns to the landing page.
    Triggered by the 'Change User' button in the sidebar.
    """
    session.clear()
    session['db_user_id'] = -1
    session['user_input'] = {'pessimism': 'Realistic'}
    return redirect(url_for('welcome'))


@app.route('/process_input', methods=['POST'])
def process_input():
    if 'db_user_id' not in session or session['db_user_id'] == -1:
        return redirect(url_for('welcome'))

    username = session['user_input']['username']
    about = request.form.get('about', '').strip()
    goal = request.form.get('goal', '').strip()
    plan = request.form.get('plan', '').strip()
    wrong = request.form.get('wrong', '').strip()
    pessimism = request.form.get('pessimism', 'Realistic')

    if not all([goal, plan]):  # Username and about are already guaranteed or handled
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
    new_pessimism = request.form.get('pessimism')

    # 1. Capture the existing level before it's updated
    old_pessimism = session['user_input'].get('pessimism', 'Realistic')
    if new_pessimism == old_pessimism:
        old_pessimism = None

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

    res = llm_logic.refine_analysis(
        session['user_input'],
        feedback,
        binary,
        session['chat_history'],
        old_pessimism
    )

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

    if 'followup' not in current:
        res = llm_logic.generate_followup(current['revised_plan'], session['user_input']['about'],
                                          session['chat_history'])
        add_to_history("user", "Construct my execution plan.")
        add_to_history("model", "Execution plan and advice generated.")

        current['followup'] = res
        session.modified = True

        # Sync the new followup data to the dedicated database column
        db_logic.update_existing_plan(
            plan_id=session['plan_db_id'],
            versions=session['versions'],
            chat_history=session['chat_history'],
            followup_data=res  # Pass the result to db_logic
        )

    return render_template('followup.html', data=current['followup'], plan=current['revised_plan'])

@app.route('/load_plan/<int:plan_id>')
def load_plan(plan_id):
    """Reloads a plan from the database into the session."""
    plan_data = db_logic.get_plan_by_id(plan_id)
    if not plan_data:
        return redirect(url_for('index'))

    # Reconstruct session
    session['plan_db_id'] = plan_data['id']
    session['db_user_id'] = plan_data['user_id']
    session['user_input'] = {
        'goal': plan_data['goal'],
        'plan': plan_data['original_plan'],
        'pessimism': plan_data['pessimism'],
        'wrong': plan_data.get('concerns', ''),
        # We need the username/about from the session or DB
        'username': session.get('user_input', {}).get('username'),
        'about': session.get('user_input', {}).get('about')
    }
    session['maze_answers'] = plan_data['maze_results']
    session['versions'] = plan_data['versions']
    session['chat_history'] = plan_data['chat_history']
    session['current_v_idx'] = len(plan_data['versions']) - 1
    session.modified = True

    # Check if the latest version has a followup
    latest_version = plan_data['versions'][-1]
    if 'followup' in latest_version:
        return redirect(url_for('followup'))
    return redirect(url_for('dashboard'))


@app.route('/reset')
def reset():
    """Clears the project progress but keeps the user profile active."""
    # Keys to keep (user profile info)
    keys_to_keep = ['db_user_id', 'user_input']
    saved_data = {k: session.get(k) for k in keys_to_keep}

    # Clear project-specific data only
    session.clear()

    # Restore user info and auto-fill the 'about' for the input page
    if saved_data['db_user_id'] != -1:
        session['db_user_id'] = saved_data['db_user_id']
        # We clear goal/plan but keep username/about for auto-fill
        session['user_input'] = {
            'username': saved_data['user_input'].get('username'),
            'about': saved_data['user_input'].get('about'),
            'pessimism': 'Realistic'  # Default for new session
        }

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=config.DEBUG, port=5000)