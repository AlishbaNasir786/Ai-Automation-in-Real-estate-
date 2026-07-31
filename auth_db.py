"""
auth_db.py — User Authentication & Database Management
Handles user signup, login, Google OAuth integration, session tokens,
role-based access control (admin / client), and persona segment persistence.

DATABASE SCHEMA (users table)
──────────────────────────────────────────────────────────────────────────────
id             TEXT  PRIMARY KEY   (UUID v4)
email          TEXT  UNIQUE        (lowercase)
password_hash  TEXT                (bcrypt via werkzeug — NULL for Google)
full_name      TEXT
phone          TEXT                (optional contact number)
auth_provider  TEXT  DEFAULT 'local'  ('local' | 'google')
google_id      TEXT  UNIQUE        (Google sub claim — NULL for local)
email_verified INTEGER DEFAULT 0  (1 = verified)
segment        TEXT                (persona key: investor / family / etc.)
role           TEXT  DEFAULT 'client' ('admin' | 'client')
created_at     TEXT                (ISO-8601)
last_login_at  TEXT                (ISO-8601)
──────────────────────────────────────────────────────────────────────────────
"""

import os
import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = os.path.join(os.path.dirname(__file__), "users_store.db")

# ── ADMIN CREDENTIALS ────────────────────────────────────────────────────────
ADMIN_EMAIL    = "admin@realestate-ai.pk"
ADMIN_PASSWORD = "Admin@2026!"
ADMIN_NAME     = "System Administrator"

# ── PRE-SEEDED CLIENT ACCOUNTS ───────────────────────────────────────────────
# These are delivered credentials. Clients can also register via Google OAuth.
SEEDED_CLIENTS = [
    {
        "email":     "client@realestate-ai.pk",
        "password":  "Client@2026!",
        "full_name": "Demo Client",
        "phone":     "+92-300-0000001",
    },
    {
        "email":     "ahmed.khan@realestate-ai.pk",
        "password":  "AhmedK@2026!",
        "full_name": "Ahmed Khan",
        "phone":     "+92-321-1234567",
    },
    {
        "email":     "sara.malik@realestate-ai.pk",
        "password":  "SaraM@2026!",
        "full_name": "Sara Malik",
        "phone":     "+92-333-7654321",
    },
]


def init_auth_db():
    """Initialize local users database. Fully idempotent — safe to call on every startup."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Primary users table
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id             TEXT PRIMARY KEY,
        email          TEXT UNIQUE NOT NULL,
        password_hash  TEXT,
        full_name      TEXT NOT NULL,
        phone          TEXT,
        auth_provider  TEXT NOT NULL DEFAULT 'local',
        google_id      TEXT UNIQUE,
        email_verified INTEGER NOT NULL DEFAULT 0,
        segment        TEXT,
        role           TEXT NOT NULL DEFAULT 'client',
        created_at     TEXT NOT NULL,
        last_login_at  TEXT
    )
    """)

    # Listing likes table
    c.execute("""
    CREATE TABLE IF NOT EXISTS listing_likes (
        id          TEXT PRIMARY KEY,
        property_id TEXT NOT NULL,
        session_key TEXT NOT NULL,
        created_at  TEXT NOT NULL,
        UNIQUE(property_id, session_key)
    )
    """)

    # Listing reviews table (property-specific, stored locally)
    c.execute("""
    CREATE TABLE IF NOT EXISTS listing_reviews (
        id            TEXT PRIMARY KEY,
        property_id   TEXT NOT NULL,
        reviewer_name TEXT NOT NULL,
        rating        INTEGER NOT NULL,
        comment       TEXT NOT NULL,
        created_at    TEXT NOT NULL
    )
    """)

    # Safe migration: add columns that may not exist in older DB files
    _safe_add_column(c, "users", "role",  "TEXT NOT NULL DEFAULT 'client'")
    _safe_add_column(c, "users", "phone", "TEXT")

    conn.commit()
    conn.close()

    # Seed system accounts
    _seed_system_accounts()


def _safe_add_column(cursor, table, column, col_def):
    """Add a column only if it doesn't already exist."""
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")
    except Exception:
        pass  # Column already exists


def _seed_system_accounts():
    """Ensure admin and all pre-seeded client accounts exist in DB."""
    _ensure_user(ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME, role="admin")
    for client in SEEDED_CLIENTS:
        _ensure_user(
            client["email"],
            client["password"],
            client["full_name"],
            role="client",
            phone=client.get("phone"),
        )


def _ensure_user(email, password, full_name, role="client", phone=None):
    """Create user if they don't exist; always enforce correct role."""
    existing = get_user_by_email(email)
    if existing:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE users SET role = ? WHERE email = ?", (role, email.lower()))
        conn.commit()
        conn.close()
        return
    create_user(email=email, password=password, full_name=full_name,
                role=role, phone=phone)


# ─────────────────────────────────────────────────────────────────────────────
# CRUD helpers
# ─────────────────────────────────────────────────────────────────────────────

def create_user(email: str, password: str = None, full_name: str = "",
                auth_provider: str = "local", google_id: str = None,
                segment: str = None, role: str = "client",
                phone: str = None) -> dict:
    """Create a new user record with hashed password."""
    import uuid
    email = email.lower().strip()
    user_id = str(uuid.uuid4())
    pw_hash = generate_password_hash(password) if password else None
    now = datetime.now().isoformat()

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("""
        INSERT INTO users
            (id, email, password_hash, full_name, phone, auth_provider, google_id,
             email_verified, segment, role, created_at, last_login_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, email, pw_hash, full_name, phone, auth_provider, google_id,
              1 if auth_provider == 'google' else 0,
              segment, role, now, now))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"error": "User with this email already exists."}

    conn.close()
    return get_user_by_id(user_id)


def get_user_by_email(email: str) -> dict:
    """Retrieve user by email."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> dict:
    """Retrieve user by UUID (excludes password_hash)."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT id, email, full_name, auth_provider, google_id,
               email_verified, segment, role, created_at, last_login_at
        FROM users WHERE id = ?
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def authenticate_user(email: str, password: str) -> dict:
    """Verify email and password."""
    user = get_user_by_email(email)
    if not user:
        return {"error": "Invalid email or password."}
    if not user.get("password_hash") or \
       not check_password_hash(user["password_hash"], password):
        return {"error": "Invalid email or password."}

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET last_login_at = ? WHERE id = ?",
              (datetime.now().isoformat(), user["id"]))
    conn.commit()
    conn.close()

    return get_user_by_id(user["id"])


def authenticate_google_user(email: str, full_name: str, google_id: str) -> dict:
    """Handle Google OAuth — find-or-create, always client role for Google sign-ins."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE google_id = ? OR email = ?",
              (google_id, email.lower().strip()))
    row = c.fetchone()
    conn.close()

    if row:
        user = dict(row)
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("UPDATE users SET last_login_at = ?, google_id = ? WHERE id = ?",
                  (datetime.now().isoformat(), google_id, user["id"]))
        conn.commit()
        conn.close()
        return get_user_by_id(user["id"])
    else:
        return create_user(email=email, full_name=full_name,
                           auth_provider="google", google_id=google_id, role="client")


def update_user_segment(user_id: str, segment: str) -> dict:
    """Update user's persona segment preference."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET segment = ? WHERE id = ?",
              (segment.lower().strip(), user_id))
    conn.commit()
    conn.close()
    return get_user_by_id(user_id)


# ── LISTING LIKES HELPERS ─────────────────────────────────────────────────────

def toggle_listing_like(property_id: str, session_key: str) -> dict:
    """Toggle a like on a listing. Returns {liked: bool, count: int}."""
    import uuid
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM listing_likes WHERE property_id=? AND session_key=?",
              (property_id, session_key))
    existing = c.fetchone()
    if existing:
        c.execute("DELETE FROM listing_likes WHERE property_id=? AND session_key=?",
                  (property_id, session_key))
        liked = False
    else:
        c.execute("INSERT INTO listing_likes (id, property_id, session_key, created_at) VALUES (?,?,?,?)",
                  (str(uuid.uuid4()), property_id, session_key, datetime.now().isoformat()))
        liked = True
    conn.commit()
    c.execute("SELECT COUNT(*) FROM listing_likes WHERE property_id=?", (property_id,))
    count = c.fetchone()[0]
    conn.close()
    return {"liked": liked, "count": count}


def get_listing_likes(property_ids: list = None) -> dict:
    """Return {property_id: count} for all or specified properties."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if property_ids:
        placeholders = ",".join("?" * len(property_ids))
        c.execute(f"SELECT property_id, COUNT(*) FROM listing_likes WHERE property_id IN ({placeholders}) GROUP BY property_id",
                  property_ids)
    else:
        c.execute("SELECT property_id, COUNT(*) FROM listing_likes GROUP BY property_id")
    rows = c.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}


def get_user_liked_properties(session_key: str) -> list:
    """Return list of property_ids that this session has liked."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT property_id FROM listing_likes WHERE session_key=?", (session_key,))
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


# ── LISTING REVIEWS HELPERS ───────────────────────────────────────────────────

def submit_listing_review(property_id: str, reviewer_name: str, rating: int, comment: str) -> dict:
    """Insert a review for a specific listing."""
    import uuid
    rating = max(1, min(5, int(rating)))
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    rev_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    try:
        c.execute("""INSERT INTO listing_reviews (id, property_id, reviewer_name, rating, comment, created_at)
                     VALUES (?,?,?,?,?,?)""",
                  (rev_id, property_id, reviewer_name.strip()[:80],
                   rating, comment.strip()[:1000], now))
        conn.commit()
        conn.close()
        return {"success": True, "id": rev_id}
    except Exception as e:
        conn.close()
        return {"success": False, "error": str(e)}


def get_listing_reviews(property_id: str) -> list:
    """Return all reviews for a specific property, newest first."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM listing_reviews WHERE property_id=? ORDER BY created_at DESC",
              (property_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_all_listing_engagement() -> dict:
    """Return aggregated engagement stats for the marketing report."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Total likes
    c.execute("SELECT COUNT(*) FROM listing_likes")
    total_likes = c.fetchone()[0]

    # Top 5 most liked listings
    c.execute("""SELECT property_id, COUNT(*) as cnt FROM listing_likes
                 GROUP BY property_id ORDER BY cnt DESC LIMIT 5""")
    top_liked = [{"property_id": r[0], "likes": r[1]} for r in c.fetchall()]

    # Total listing reviews
    c.execute("SELECT COUNT(*) FROM listing_reviews")
    total_reviews = c.fetchone()[0]

    # Per-property review stats
    c.execute("""SELECT property_id, COUNT(*) as cnt, AVG(rating) as avg_r
                 FROM listing_reviews GROUP BY property_id ORDER BY cnt DESC""")
    per_property = [{"property_id": r[0], "reviews": r[1], "avg_rating": round(r[2], 1)} for r in c.fetchall()]

    conn.close()
    return {
        "total_likes": total_likes,
        "top_liked_listings": top_liked,
        "total_listing_reviews": total_reviews,
        "per_property_stats": per_property,
    }


# Ensure DB + seeded accounts exist on import
init_auth_db()
