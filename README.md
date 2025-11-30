# 🏆 Libya FPL - Fantasy Premier League Tracker

A comprehensive web application for tracking multiple Fantasy Premier League (FPL) Head-to-Head leagues for the Libyan FPL community. Built with Flask and designed with a mobile-first Arabic RTL interface.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

### Live Dashboard
- **Real-time standings** with live points calculation during gameweeks
- **Automatic bonus points** calculation before official FPL updates
- **Auto-substitution simulation** following FPL rules (formation validation, GK↔GK only)
- **Captain & Vice-Captain logic** with proper multiplier handling

### Head-to-Head Tracking
- **Live H2H match results** with win/draw/loss indicators
- **Points differential** between opponents
- **Projected league standings** based on live results

### Manager Comparison
- **Unique players analysis** showing differential picks between opponents
- **Player status indicators** (played, benched, pending)
- **Count-based differentials** (e.g., "Salah x2" if one team has 2 more)

### Team-Based Leagues
- Support for **team H2H leagues** where each team has 3 managers
- **Combined team points** calculation
- **Captain grouping** with multiplier notation (e.g., "Salah x2, Haaland")

### Additional Features
- **Rank change arrows** (↑↓) comparing to previous gameweek
- **Chip tracking** (Wildcard, Bench Boost, Triple Captain, Free Hit)
- **Qualification zone highlighting** for elimination-style leagues
- **Mobile-responsive design** with Arabic RTL support

---

## 🏟️ Supported Leagues

| League | Type | Teams/Managers | Description |
|--------|------|----------------|-------------|
| **دوري النخبة** (Elite League) | Individual H2H | 20 managers | Premier individual H2H league |
| **The 100** | Classic (Elimination) | 100+ managers | Weekly elimination, top 99 qualify |
| **دوري المدن** (Cities League) | Team H2H | 20 teams × 3 managers | Libyan cities competition |
| **الدوري الليبي** (Libyan League) | Team H2H | 20 teams × 3 managers | Libyan clubs competition |
| **البطولة العربية** (Arab Championship) | Team H2H | 20 teams × 3 managers | Arab clubs competition |

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11+, Flask 3.0+
- **Database:** PostgreSQL (production), SQLite (development)
- **ORM:** SQLAlchemy / Flask-SQLAlchemy
- **Data Processing:** Pandas
- **HTTP Client:** Requests
- **Server:** Gunicorn
- **Hosting:** Render.com

---

## 📦 Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- PostgreSQL (for production) or SQLite (for development)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/libya-fpl.git
   cd libya-fpl
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open in browser**
   ```
   http://localhost:5000
   ```

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory:

```env
# FPL API Authentication (get from browser cookies when logged into FPL)
FPL_SESSION_ID=your_session_id_here
FPL_CSRF_TOKEN=your_csrf_token_here

# Database URL (PostgreSQL for production)
DATABASE_URL=postgresql://user:password@host:port/database

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```

### Getting FPL Cookies

1. Log in to [Fantasy Premier League](https://fantasy.premierleague.com/)
2. Open browser Developer Tools (F12)
3. Go to Application → Cookies
4. Copy `sessionid` and `csrftoken` values

---

## 🚀 Deployment (Render.com)

### One-Click Deploy

1. Fork this repository
2. Connect to [Render.com](https://render.com)
3. Create a new Web Service
4. Connect your GitHub repository
5. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
6. Add environment variables in Render dashboard
7. Deploy!

### render.yaml Configuration

```yaml
services:
  - type: web
    name: libya-fpl
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: FPL_SESSION_ID
        sync: false
      - key: FPL_CSRF_TOKEN
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: libya-fpl-db
          property: connectionString

databases:
  - name: libya-fpl-db
    plan: free
```

---

## 📁 Project Structure

```
libya-fpl/
├── app.py                 # Main Flask application
├── config.py              # Configuration and Arabic translations
├── models.py              # Database models (SQLAlchemy)
├── requirements.txt       # Python dependencies
├── Procfile              # Gunicorn configuration
├── render.yaml           # Render.com deployment config
│
├── core/                  # Core logic modules
│   ├── __init__.py
│   ├── fpl_api.py        # FPL API wrapper
│   ├── dashboard.py      # Elite League logic
│   ├── the100.py         # The 100 League logic
│   ├── cities_league.py  # Cities League logic
│   ├── libyan_league.py  # Libyan League logic
│   ├── arab_league.py    # Arab Championship logic
│   └── stats.py          # Statistics calculations
│
├── templates/             # Jinja2 HTML templates
│   ├── home.html         # Landing page
│   ├── dashboard.html    # Elite League dashboard
│   ├── the100_dashboard.html
│   ├── cities_dashboard.html
│   ├── libyan_dashboard.html
│   ├── arab_dashboard.html
│   ├── stats.html        # Statistics page
│   └── partials/
│       └── standings_table.html
│
└── static/                # Static assets
    ├── css/
    │   ├── style.css     # Main stylesheet
    │   └── the100.css    # The 100 dark theme
    ├── elite_league_logo.png
    ├── the100_logo.png
    ├── cities_logo.png
    ├── libyan_logo.png
    └── arab_logo.png
```

---

## 🔄 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Home page with league selection |
| `GET /league/elite` | Elite League dashboard |
| `GET /league/elite/stats` | Elite League statistics |
| `GET /league/the100` | The 100 League dashboard |
| `GET /league/cities` | Cities League dashboard |
| `GET /league/libyan` | Libyan League dashboard |
| `GET /league/arab` | Arab Championship dashboard |
| `GET /api/manager/<id>/history` | Manager history JSON |

---

## 📊 Points Calculation Rules

### Individual Leagues (Elite, The 100)
- Standard FPL points with live bonus calculation
- Captain: 2× points (3× for Triple Captain)
- Auto-subs follow FPL formation rules

### Team-Based Leagues (Cities, Libyan, Arab)
- Sum of 3 managers' points per team
- **Triple Captain treated as 2×** (league rule)
- **Bench Boost ignored** (only starting 11 counts)
- Auto-subs calculated per manager

---

## 🎨 Design Features

- **RTL Layout:** Full Arabic right-to-left support
- **Mobile-First:** Optimized for mobile viewing
- **Dark Theme:** The 100 League uses dark metallic theme
- **Color Coding:**
  - 🟢 Green: Win / Safe zone / Played
  - 🔴 Red: Loss / Danger zone / Benched
  - 🟡 Yellow: Draw / Pending
  - 🟣 Purple: League points highlight

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Fantasy Premier League](https://fantasy.premierleague.com/) for the API
- The Libyan FPL community (قروب عشاق الفانتازي في ليبيا)
- All league commissioners and participants

---

## 📧 Contact

For questions or support, reach out to the Libyan FPL community group.

---

<p align="center">
  Made with ❤️ for the Libyan FPL Community
</p>
