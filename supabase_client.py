# supabase_client.py
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timezone
from typing import Optional, Dict, Any

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Set SUPABASE_URL and SUPABASE_KEY in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------- Profile helpers ----------

def get_profile(telegram_id: int) -> Optional[Dict[str, Any]]:
    try:
        res = supabase.table("profiles").select("*").eq("telegram_id", str(telegram_id)).execute()
        if res.data and len(res.data) > 0:
            return res.data[0]
        else:
            print(f"No profile found for {telegram_id}")
            return None
    except Exception as e:
        print("Error fetching profile:", e)
        return None


def create_profile(telegram_id: int, name: str = None, preferences: dict = None) -> Dict[str, Any]:
    payload = {
        "telegram_id": str(telegram_id),
        "name": name,
        "preferences": preferences or {},
        "memory": "",
        "onboarding_step": 0,
        "last_interaction": datetime.now(timezone.utc).isoformat()
    }
    res = supabase.table("profiles").insert(payload).execute()
    if res.data:
        print(f"Created profile for {telegram_id}")
        return res.data[0]
    else:
        print("Failed to create profile:", res)
        return payload


def upsert_profile(telegram_id: int, updates: dict) -> Dict[str, Any]:
    updates["telegram_id"] = str(telegram_id)
    res = supabase.table("profiles").upsert(updates, on_conflict="telegram_id").execute()
    return res.data[0] if res.data else updates


def update_profile_field(telegram_id: int, field: str, value):
    updates = {field: value, "last_interaction": datetime.now(timezone.utc).isoformat()}
    res = supabase.table("profiles").update(updates).eq("telegram_id", str(telegram_id)).execute()
    return res.data[0] if res.data else updates


# ---------- Memory & logs ----------

def append_memory(telegram_id: int, text: str):
    profile = get_profile(telegram_id)
    if not profile:
        create_profile(telegram_id)
        profile = get_profile(telegram_id)
    current = profile.get("memory") or ""
    new_memory = current + ("\n" if current else "") + text
    update_profile_field(telegram_id, "memory", new_memory)
    return new_memory


def log_interaction(telegram_id: int, role: str, content: str):
    try:
        supabase.table("interaction_logs").insert({
            "telegram_id": str(telegram_id),
            "role": role,
            "content": content,
        }).execute()
    except Exception as e:
        print("Error logging interaction:", e)
