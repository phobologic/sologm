"""
Create a new Alembic migration.
"""
import os
import sys
import subprocess
import argparse

def create_migration(message: str, alembic_dir: str = None) -> None:
    """
    Create a new Alembic migration.
    
    Args:
        message: Message describing the migration.
        alembic_dir: Directory where Alembic files are stored.
                    If None, uses the current directory.
    """
    # Get the alembic directory
    if alembic_dir is None:
        alembic_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the alembic directory
    os.chdir(alembic_dir)
    
    # Create the migration
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", message])
    
    print(f"Migration created in {alembic_dir}/alembic/versions/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new Alembic migration.")
    parser.add_argument("message", help="Message describing the migration.")
    parser.add_argument("--dir", help="Directory where Alembic files are stored.")
    args = parser.parse_args()
    
    create_migration(args.message, args.dir) 