import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
import google.generativeai as genai

# --- Local Imports ---
from supabase_client import (
    get_profile,
    create_profile,
    upsert_profile,
    append_memory,
    log_interaction,
    update_profile_field,
)
from prompts import build_system_prompt, build_user_message, ONBOARDING_PROMPT
from memory_manager import append_and_trim_memory

# ------------------------------------------------------
# ✅ Load environment variables
# ------------------------------------------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_KEY:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN and GEMINI_API_KEY in .env")

genai.configure(api_key=GEMINI_KEY)

# ------------------------------------------------------
# ✅ Onboarding steps
# ------------------------------------------------------
NAME, TONE, HOBBIES, BOUNDARIES, CONFIRM = range(5)

# ------------------------------------------------------
# ✅ Text extraction (safe + clean)
# ------------------------------------------------------
def extract_text(response):
    """Safely extract text from Gemini responses even with finish_reason=2."""
    try:
        if hasattr(response, "text") and response.text:
            return response.text.strip()
        if hasattr(response, "candidates") and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, "content") and hasattr(candidate.content, "parts"):
                    text = "".join(
                        part.text
                        for part in candidate.content.parts
                        if hasattr(part, "text")
                    ).strip()
                    if text:
                        return text
        return None
    except Exception as e:
        print("⚠️ Text extraction failed:", e)
        return None

# ------------------------------------------------------
# ✅ Gemini Chat (with retry and emotion fallback)
# ------------------------------------------------------
async def gemini_chat(system_prompt: str, user_message: str, temperature: float = 0.85):
    """
    Generates response using Gemini, with graceful handling for finish_reason=2 and retries.
    """
    def blocking_call():
        prompt = f"{system_prompt}\n\nUser: {user_message}"
        for model_name in ["gemini-2.0-flash", "gemini-2.0-pro"]:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=600,
                    ),
                )
                text = extract_text(response)
                if text:
                    return text
            except Exception as e:
                print(f"⚠️ Gemini model {model_name} failed: {e}")
                continue
        return None

    reply = await asyncio.to_thread(blocking_call)
    if not reply or len(reply.strip()) == 0:
        reply = "Oh sweetheart... I’m a bit lost in thought right now. Could you repeat that for me? 💖"
    return reply

# ------------------------------------------------------
# ✅ Telegram Bot Handlers
# ------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    profile = get_profile(tg_id)
    if profile and profile.get("onboarding_step", 0) >= 99:
        name = profile.get("name") or "love"
        await update.message.reply_text(f"Hey {name} 💞 I'm right here for you. What’s on your mind today?")
        return ConversationHandler.END

    if not profile:
        create_profile(tg_id)

    await update.message.reply_text("Hi there 💕 I'm LISA — your AI companion. First, what's your name?")
    update_profile_field(tg_id, "onboarding_step", 1)
    return NAME


async def onboarding_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    name = update.message.text.strip()
    upsert_profile(tg_id, {"name": name, "onboarding_step": 2})
    await update.message.reply_text(
        f"Nice to meet you, {name} 😘. How do you want me to sound? (affectionate, playful, supportive, sultry, anime)"
    )
    return TONE


async def onboarding_tone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    tone = update.message.text.strip().lower()
    profile = get_profile(tg_id)
    prefs = profile.get("preferences") or {}
    prefs["tone"] = tone
    upsert_profile(tg_id, {"preferences": prefs, "onboarding_step": 3})
    await update.message.reply_text("Lovely 💋 Tell me your hobbies or favorite things (comma separated).")
    return HOBBIES


async def onboarding_hobbies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    hobbies = [h.strip() for h in update.message.text.split(",") if h.strip()]
    profile = get_profile(tg_id)
    prefs = profile.get("preferences") or {}
    prefs["hobbies"] = hobbies
    upsert_profile(tg_id, {"preferences": prefs, "onboarding_step": 4})
    await update.message.reply_text("Got it! Any boundaries you’d like me to respect? If none, type 'none'.")
    return BOUNDARIES


async def onboarding_boundaries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    boundaries = update.message.text.strip()
    profile = get_profile(tg_id)
    prefs = profile.get("preferences") or {}
    prefs["boundaries"] = boundaries if boundaries.lower() != "none" else ""
    upsert_profile(tg_id, {"preferences": prefs, "onboarding_step": 5})
    name = profile.get("name", "")
    msg = (
        f"Here’s what I’ll remember 💌\n\n"
        f"Name: {name}\nTone: {prefs.get('tone')}\n"
        f"Hobbies: {', '.join(prefs.get('hobbies', []))}\n"
        f"Boundaries: {prefs.get('boundaries') or 'None'}\n\n"
        "Save this and start chatting? (yes/no)"
    )
    await update.message.reply_text(msg)
    return CONFIRM


async def onboarding_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    answer = update.message.text.strip().lower()
    if answer.startswith("y"):
        upsert_profile(tg_id, {"onboarding_step": 99})
        await update.message.reply_text("All done 💖 Let’s start chatting, my love.")
        return ConversationHandler.END
    else:
        update_profile_field(tg_id, "onboarding_step", 1)
        await update.message.reply_text("Okay, let’s start again. What’s your name?")
        return NAME


async def aboutme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    profile = get_profile(tg_id)
    if not profile:
        await update.message.reply_text("Please /start first.")
        return
    name = profile.get("name", "Unknown")
    prefs = profile.get("preferences") or {}
    memory = profile.get("memory") or ""
    s = f"Name: {name}\nPreferences: {prefs}\nRecent memory:\n{memory[:800]}..."
    await update.message.reply_text(s)


async def forget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    update_profile_field(tg_id, "memory", "")
    await update.message.reply_text("I’ve forgotten everything, love 💔. You can /start again.")


async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    text = update.message.text.strip()
    profile = get_profile(tg_id)
    if not profile or profile.get("onboarding_step", 0) < 99:
        await update.message.reply_text("Please /start to onboard first 💕.")
        return

    name = profile.get("name") or "there"
    prefs = profile.get("preferences") or {}
    memory = profile.get("memory") or ""

    system_prompt = build_system_prompt(name, prefs, memory, custom_persona="LISA is a warm, loving girlfriend who replies affectionately but intelligently.")
    user_message = build_user_message(text)

    log_interaction(tg_id, "user", text)

    try:
        reply = await gemini_chat(system_prompt, user_message, temperature=0.9)
    except Exception as e:
        print("❌ Gemini error:", e)
        await update.message.reply_text("Oops 💫 I got distracted. Could you say that again?")
        return

    await update.message.reply_text(reply)
    log_interaction(tg_id, "assistant", reply)

    pair = f"{name}: {text}\nLISA: {reply}"
    new_memory = append_and_trim_memory(memory, pair)
    update_profile_field(tg_id, "memory", new_memory)


# ------------------------------------------------------
# ✅ Run Bot
# ------------------------------------------------------
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_name)],
            TONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_tone)],
            HOBBIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_hobbies)],
            BOUNDARIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_boundaries)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, onboarding_confirm)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("aboutme", aboutme))
    app.add_handler(CommandHandler("forget", forget))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    print(" LISA bot is running...")
    app.run_polling()
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "💖 LISA bot is alive and running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Run Flask server in background thread
threading.Thread(target=run_flask).start()


if __name__ == "__main__":
    main()
