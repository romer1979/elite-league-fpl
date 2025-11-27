# -*- coding: utf-8 -*-
"""
Elite League FPL App - Single Page Dashboard
"""

from flask import Flask, render_template, jsonify
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import LEAGUE_ID, ARABIC
from core.dashboard import get_dashboard
from core.stats import get_league_stats, get_manager_history
from models import db, save_standings, calculate_rank_change

app = Flask(__name__)

# Database configuration
database_url = os.environ.get('DATABASE_URL', 'sqlite:///elite_league.db')
# Fix for Render PostgreSQL URL (postgres:// -> postgresql://)
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'elite-league-secret-key-2024')

# Initialize database
db.init_app(app)

# Create tables on first request
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    """Main dashboard page - single page with everything"""
    data = get_dashboard()
    
    # Calculate rank changes from database
    if data.get('success') and data.get('standings'):
        gameweek = data.get('gameweek', 1)
        
        for team in data['standings']:
            entry_id = team.get('entry_id')
            current_rank = team.get('rank', 0)
            
            # Get rank change from previous gameweek
            rank_change = calculate_rank_change(gameweek, entry_id, current_rank)
            team['rank_change'] = rank_change
        
        # Save current standings to database (only if gameweek is finished or live)
        if data.get('gw_finished') or data.get('is_live'):
            save_standings(gameweek, data['standings'])
    
    return render_template('dashboard.html', data=data, ar=ARABIC)


@app.route('/stats')
def stats():
    """League statistics page"""
    data = get_league_stats()
    return render_template('stats.html', data=data, ar=ARABIC)


@app.route('/api/comparison')
def comparison_data():
    """API endpoint for manager comparison data"""
    data = get_manager_history()
    return jsonify(data)


@app.route('/api/dashboard')
def api_dashboard():
    """API endpoint for AJAX updates"""
    data = get_dashboard()
    data['timestamp'] = datetime.now().strftime('%H:%M:%S')
    return jsonify(data)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('dashboard.html', data={'success': False, 'error': 'Page not found'}, ar=ARABIC), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('dashboard.html', data={'success': False, 'error': 'Server error'}, ar=ARABIC), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
