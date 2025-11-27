# Elite League FPL Tracker 🏆

A Fantasy Premier League H2H League tracker with live standings, statistics, and manager comparison.

## Features

- 📊 Live standings with rank changes
- ⚔️ H2H fixture results
- 📈 Manager comparison charts (points & ranks)
- 👑 Captain & chip usage stats
- 🍀 Lucky/Unlucky manager of the week
- 🔄 Auto-refresh during live gameweeks

## Local Development

### Prerequisites
- Python 3.10+
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/elite-league.git
cd elite-league

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Visit: http://localhost:5001

---

## Render Deployment Guide

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/elite-league.git
git push -u origin main
```

### Step 2: Deploy on Render

#### Option A: Using render.yaml (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and create:
   - PostgreSQL database
   - Web service
5. Click **"Apply"** and wait for deployment

#### Option B: Manual Setup

1. **Create PostgreSQL Database:**
   - Go to Render Dashboard → **"New"** → **"PostgreSQL"**
   - Name: `elite-league-db`
   - Plan: Free (or Starter for better performance)
   - Click **"Create Database"**
   - Copy the **Internal Database URL**

2. **Create Web Service:**
   - Go to Render Dashboard → **"New"** → **"Web Service"**
   - Connect your GitHub repository
   - Settings:
     - **Name:** `elite-league`
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn app:app`
   - Add Environment Variable:
     - `DATABASE_URL` = (paste Internal Database URL)
   - Click **"Create Web Service"**

### Step 3: Access Your App

Your app will be live at: `https://elite-league.onrender.com`

---

## Keep Free Tier Awake (Optional)

If using the free tier, the app sleeps after 15 minutes of inactivity.

**Solution:** Use [cron-job.org](https://cron-job.org) to ping your app every 14 minutes:

1. Create account at cron-job.org
2. Add new cron job:
   - URL: `https://elite-league.onrender.com/`
   - Schedule: Every 14 minutes
3. Save and activate

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes (for Render) |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `PORT` | Server port | Default: 5001 |

---

## Database Models

### StandingsHistory
Stores standings snapshot for each gameweek:
- Player rank, league points, GW points
- Overall rank, captain, chip used
- Match result and opponent

### FixtureResult
Stores H2H fixture results per gameweek

---

## Tech Stack

- **Backend:** Flask, SQLAlchemy
- **Database:** PostgreSQL (Render) / SQLite (local)
- **Frontend:** HTML, CSS, JavaScript, Chart.js
- **Deployment:** Render, Gunicorn

---

## License

MIT License

---

## Credits

- FPL API: https://fantasy.premierleague.com/api/
- Created by: Rabie Al-Shtewi
