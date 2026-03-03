
import sqlite3
import os

# --- Database Setup ---
# Get the absolute path of the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "db", "plan.db")

def get_db_connection():
    """Establishes a connection to the database."""
    # Ensure the db directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates the template_plan table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS template_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER NOT NULL, -- 0 for Monday, 1 for Tuesday, etc.
            period TEXT NOT NULL,      -- 'morning', 'afternoon', 'evening'
            content TEXT,
            UNIQUE(day_of_week, period)
        )
    ''')
    conn.commit()
    conn.close()

# --- Data Access Functions ---

def get_all_plans():
    """Retrieves all plans from the template_plan table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM template_plan')
    plans = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return plans

def save_plan(day_of_week, period, content):
    """Saves or updates a plan in the template_plan table."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if a plan for this slot already exists
    cursor.execute(
        'SELECT id FROM template_plan WHERE day_of_week = ? AND period = ?',
        (day_of_week, period)
    )
    existing_plan = cursor.fetchone()

    if existing_plan:
        # Update existing plan
        cursor.execute(
            'UPDATE template_plan SET content = ? WHERE id = ?',
            (content, existing_plan['id'])
        )
    else:
        # Insert new plan
        cursor.execute(
            'INSERT INTO template_plan (day_of_week, period, content) VALUES (?, ?, ?)',
            (day_of_week, period, content)
        )
    
    conn.commit()
    conn.close()
