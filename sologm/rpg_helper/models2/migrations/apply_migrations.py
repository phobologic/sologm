"""
Apply Alembic migrations.
"""
import os
import sys
import subprocess
import argparse

def apply_migrations(db_path: str = None, alembic_dir: str = None) -> None:
    """
    Apply Alembic migrations.
    
    Args:
        db_path: Path to the database file. If None, uses the default path.
        alembic_dir: Directory where Alembic files are stored.
                    If None, uses the current directory.
    """
    # Get the database path
    if db_path is None:
        # Default to a file in the user's home directory
        home_dir = os.path.expanduser("~")
        db_dir = os.path.join(home_dir, ".sologm")
        db_path = os.path.join(db_dir, "rpg_helper.db")
    
    # Get the alembic directory
    if alembic_dir is None:
        alembic_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the alembic directory
    os.chdir(alembic_dir)
    
    # Apply the migrations
    subprocess.run(["alembic", "upgrade", "head", "-x", f"db_path={db_path}"])
    
    print(f"Migrations applied to {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Apply Alembic migrations.")
    parser.add_argument("--db", help="Path to the database file.")
    parser.add_argument("--dir", help="Directory where Alembic files are stored.")
    args = parser.parse_args()
    
    apply_migrations(args.db, args.dir) 