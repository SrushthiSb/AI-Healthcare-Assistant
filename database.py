
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "careflow.db"


def get_connection():
    """Connect to the CareFlow AI SQLite database."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    """Create the appointment table if it does not exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                contact TEXT NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                note TEXT,
                status TEXT NOT NULL DEFAULT 'Pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def save_appointment(
    full_name,
    contact,
    appointment_date,
    appointment_time,
    note="",
):
    """Save an appointment request and return its ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO appointments (
                full_name,
                contact,
                appointment_date,
                appointment_time,
                note
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                full_name.strip(),
                contact.strip(),
                appointment_date,
                appointment_time,
                note.strip(),
            ),
        )

        return cursor.lastrowid


def get_appointment(appointment_id):
    """Retrieve one appointment request by its ID."""
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT id, full_name, contact, appointment_date,
                   appointment_time, note, status, created_at
            FROM appointments
            WHERE id = ?
            """,
            (appointment_id,),
        ).fetchone()

    return dict(row) if row else None
