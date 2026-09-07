"""SchemeMatch AI - Root Database Seed Script.
Runs initial database migration and seeds schemes, rules, benefits, CSC centers, and demo users.
Idempotent: safe to run multiple times without creating duplicate records.
"""
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Ensure backend directory is in sys.path
BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if not os.path.exists(BASE_DIR):
    BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")

sys.path.insert(0, os.path.abspath(BASE_DIR))

from app.core.database import init_db
from scripts.seed_all import seed

if __name__ == "__main__":
    print("🚀 Initializing database schema...")
    init_db()
    print("🌱 Running database seed...")
    seed()
