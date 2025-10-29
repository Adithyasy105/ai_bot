# AI Telegram Bot

LISA is a friendly AI companion built using **Python**, **Supabase**, and **Gemini AI**.
She remembers conversations, learns your preferences, and chats naturally — just like a thoughtful AI friend 💬.

---

## 🚀 Features

* 🧠 **Persistent Memory** — Stores and summarizes past chats using Supabase + Gemini.
* 💬 **Natural Conversations** — Powered by Google Gemini API for human-like dialogue.
* 👩‍💻 **User Profiles** — Automatically creates a profile for each Telegram user.
* 🕊️ **Lightweight & Fast** — Built on `python-telegram-bot` and hosted easily.
* ☁️ **Deployed Free** — Works perfectly on Render, Railway, or Deta.

---

## 🧩 Project Structure

```
ai_girlfriend_bot/
│
├─ bot.py                       # Main bot logic (Telegram handlers + Flask keep-alive)
├─ supabase_client.py           # Supabase helper functions
├─ prompts.py                   # Persona & prompt templates
├─ memory_manager.py            # Summarization and memory management
├─ requirements.txt             # Python dependencies
├─ .env.example                 # Example environment variables
├─ README.md                    # Project documentation
└─ sql/
   └─ create_tables.sql         # Supabase schema creation script
```

---

## ⚙️ Environment Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/ai_bot.git
cd ai_bot
```

### 2️⃣ Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Configuration

Create a `.env` file in the project root:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
GEMINI_API_KEY=your-gemini-api-key
```

> Rename `.env.example` to `.env` and fill in your actual credentials.

---

## 🧠 Supabase Setup

1. Go to **[https://supabase.com](https://supabase.com)** and create a free project.
2. Open **SQL Editor → New Query**.
3. Copy and paste the SQL from:

   ```
   sql/create_tables.sql
   ```
4. Click **Run** to create tables (`profiles`, `messages`, etc.).
5. Copy your **Project URL** and **anon key** from:
   **Settings → API → Project API Keys**.

---

## 🧪 Run Locally

```bash
python bot.py
```

You should see:

```
LISA bot is running...
```

Then open your bot on Telegram (via BotFather link) and send `/start`.

---

## ☁️ Free Deployment Options

### 🟣 **Option 1: Render (Recommended)**

1. Create an account → [https://render.com](https://render.com)
2. Click **New → Web Service → Connect GitHub Repo**
3. Build Command: *(leave empty)*
4. Start Command:

   ```
   python bot.py
   ```
5. Add `.env` variables under “Environment Variables”.
6. Click **Deploy**.

### 🟢 **Option 2: Railway**

1. Visit [https://railway.app](https://railway.app)
2. Create new project → Deploy from GitHub.
3. Add environment variables (same as `.env`).
4. Railway automatically runs `python bot.py`.

### 🟡 **Option 3: Deta Space**

1. Install Deta CLI:

   ```
   pip install deta
   ```
2. Login:

   ```
   deta login
   ```
3. Deploy:

   ```
   deta deploy
   ```

---

## 🛠 Keep-Alive Endpoint (For Render/Railway)

To prevent the bot from sleeping, `bot.py` includes a simple Flask route:

```python
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "LISA bot is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()
```

You can use **UptimeRobot** to ping this URL every 5 minutes.

---

## 🧾 License

MIT License © 2025 — Created by [Your Name]
Feel free to modify, fork, and build upon this project.

---

## 💡 Example Bot Info (for BotFather)

**Name:** LISA — AI Girlfriend
**About:** LISA — friendly AI assistant that remembers you, chats naturally, and gives lovely replies
**Description:**
LISA is your personal AI companion — she remembers your chats, learns your preferences.
You can ask questions, get advice, or just talk about your day. She’s thoughtful, fast, and always ready to listen.

**Privacy Policy:**
[https://telegram.org/privacy-tpa](https://telegram.org/privacy-tpa)

---

## ❤️ Credits

* [Supabase](https://supabase.com) — Database & auth
* [Google Gemini API](https://ai.google.dev) — AI conversations
* [python-telegram-bot](https://python-telegram-bot.org) — Telegram integration
* [Render](https://render.com) — Free hosting
