from supabase import create_client, Client
import config

supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def sync_user(username, about):
    """Upserts the user and returns their database ID."""
    response = supabase.table("users").upsert({
        "username": username,
        "about": about
    }, on_conflict="username").execute()
    return response.data[0]['id']


def create_plan_entry(user_id, user_input, maze_results, versions, chat_history, followup_data=None):
    """Inserts the initial plan after the maze is completed."""
    response = supabase.table("plans").insert({
        "user_id": user_id,
        "goal": user_input['goal'],
        "original_plan": user_input['plan'],
        "pessimism": user_input['pessimism'],
        "concerns": user_input.get('wrong', ''),
        "maze_results": maze_results,
        "versions": versions,
        "chat_history": chat_history,
        "followup": followup_data  # Save follow-up data here
    }).execute()
    return response.data[0]['id']


def update_existing_plan(plan_id, versions, chat_history, pessimism=None, followup_data=None):
    """Updates the plan row with new versions, adjusted pessimism, or followup data."""
    update_data = {
        "versions": versions,
        "chat_history": chat_history
    }
    if pessimism:
        update_data["pessimism"] = pessimism
    if followup_data:
        update_data["followup"] = followup_data # Update the dedicated column

    supabase.table("plans").update(update_data).eq("id", plan_id).execute()


def get_user_plans(username):
    """Retrieves all plans for a specific username to allow reloading."""
    # First get user id
    user_res = supabase.table("users").select("id").eq("username", username).execute()
    if not user_res.data:
        return []

    plans_res = supabase.table("plans") \
        .select("*") \
        .eq("user_id", user_res.data[0]['id']) \
        .order("id", desc=True) \
        .execute()
    return plans_res.data


def get_all_users():
    """Fetches all users from the database for the dropdown."""
    response = supabase.table("users").select("id, username").order("username").execute()
    return response.data


def add_user(username, about):
    """Adds a new user and returns the new user object."""
    response = supabase.table("users").insert({
        "username": username,
        "about": about
    }).execute()
    return response.data[0]


def get_plan_by_id(plan_id):
    """Fetches a specific plan by ID."""
    response = supabase.table("plans").select("*").eq("id", plan_id).single().execute()
    return response.data

