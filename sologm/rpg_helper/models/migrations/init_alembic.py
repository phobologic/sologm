"""
Initialize Alembic for database migrations.
"""
import os
import sys
import subprocess
import argparse

def init_alembic(alembic_dir: str = None) -> None:
    """
    Initialize Alembic for database migrations.
    
    Args:
        alembic_dir: Directory where Alembic files will be stored.
                    If None, uses the current directory.
    """
    # Get the alembic directory
    if alembic_dir is None:
        alembic_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the directory if it doesn't exist
    if not os.path.exists(alembic_dir):
        os.makedirs(alembic_dir)
    
    # Change to the alembic directory
    os.chdir(alembic_dir)
    
    # Initialize Alembic
    subprocess.run(["alembic", "init", "alembic"])
    
    # Update the alembic.ini file
    alembic_ini = os.path.join(alembic_dir, "alembic.ini")
    with open(alembic_ini, "r") as f:
        lines = f.readlines()
    
    with open(alembic_ini, "w") as f:
        for line in lines:
            if line.startswith("sqlalchemy.url = "):
                # Use a placeholder that will be replaced at runtime
                f.write("sqlalchemy.url = sqlite:///%(db_path)s\n")
            else:
                f.write(line)
    
    # Update the env.py file
    env_py = os.path.join(alembic_dir, "alembic", "env.py")
    with open(env_py, "r") as f:
        lines = f.readlines()
    
    with open(env_py, "w") as f:
        for line in lines:
            if line.startswith("from alembic import context"):
                f.write("from alembic import context\n")
                f.write("import os\n")
                f.write("import sys\n\n")
                f.write("# Add the parent directory to the path so we can import the package\n")
                f.write("sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))\n\n")
                f.write("from sologm.rpg_helper.models2.base import BaseModel\n")
            elif line.startswith("target_metadata = None"):
                f.write("target_metadata = BaseModel.metadata\n")
            else:
                f.write(line)
    
    print(f"Alembic initialized in {alembic_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Alembic for database migrations.")
    parser.add_argument("--dir", help="Directory where Alembic files will be stored.")
    args = parser.parse_args()
    
    init_alembic(args.dir) 