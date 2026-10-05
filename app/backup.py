import os
import shutil
import subprocess
from datetime import datetime
import json

BACKUP_DIR="backups"
MODEL_PATH="app/model/fraud_model.pkl"
DB_NAME="fraud_detection"
DB_USER="root"
DB_HOST="localhost"

# Read password from config
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_URL

# Extract password from DATABASE_URL
# Format: mysql+pymysql://root:password@localhost/fraud_detection
def extract_db_password(url):
    try:
        part=url.split("://")[1]        # root:password@localhost/fraud_detection
        credentials=part.split("@")[0]  # root:password
        password=credentials.split(":")[1]  # password
        # Decode %40 back to @ if present
        password=password.replace("%40", "@")
        return password
    except Exception:
        return ""

DB_PASSWORD=extract_db_password(DATABASE_URL)


def create_backup_folder():
    timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    folder=os.path.join(BACKUP_DIR, f"backup_{timestamp}")
    os.makedirs(folder, exist_ok=True)
    print(f"Backup folder created: {folder}")
    return folder, timestamp

def backup_model(backup_folder):
    print("\nBacking up model...")
    if os.path.exists(MODEL_PATH):
        dest=os.path.join(backup_folder, "fraud_model.pkl")
        shutil.copy2(MODEL_PATH, dest)
        size=os.path.getsize(dest)
        print(f"Model backed up: {dest} ({size} bytes)")
        return True
    else:
        print(f"Model file not found at {MODEL_PATH}")
        return False

def backup_database(backup_folder):
    print("\nBacking up database...")
    dump_path=os.path.join(backup_folder, f"{DB_NAME}.sql")

    # mysqldump command
    command=[
        "mysqldump",
        f"-u{DB_USER}",
        f"-p{DB_PASSWORD}",
        f"-h{DB_HOST}",
        DB_NAME
    ]

    try:
        with open(dump_path, "w") as f:
            result=subprocess.run(
                command,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True
            )

        if result.returncode==0:
            size = os.path.getsize(dump_path)
            print(f"Database backed up: {dump_path} ({size} bytes)")
            return True
        else:
            print(f"Database backup failed: {result.stderr}")
            return False

    except FileNotFoundError:
        print("mysqldump not found — adding MySQL to PATH first")
        return False



def save_manifest(backup_folder, timestamp, model_ok, db_ok):
    manifest={
        "timestamp":timestamp,
        "model_backup":"SUCCESS" if model_ok else "FAILED",
        "database_backup":"SUCCESS" if db_ok else "FAILED",
        "overall_status":"SUCCESS" if (model_ok and db_ok) else "PARTIAL"
    }

    path=os.path.join(backup_folder, "manifest.json")
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"\nManifest saved: {path}")
    return manifest


def cleanup_old_backups(keep=7):
    if not os.path.exists(BACKUP_DIR):
        return

    backups=sorted([
        d for d in os.listdir(BACKUP_DIR)
        if d.startswith("backup_")
    ])

    if len(backups) > keep:
        to_delete=backups[:len(backups) - keep]
        for folder in to_delete:
            path=os.path.join(BACKUP_DIR, folder)
            shutil.rmtree(path)
            print(f"Deleted old backup: {folder}")

def run_backup():
    print("="*50)
    print("FRAUD DETECTION SYSTEM — BACKUP STARTED")
    print("="*50)

    backup_folder, timestamp = create_backup_folder()
    model_ok= backup_model(backup_folder)
    db_ok=backup_database(backup_folder)
    manifest=save_manifest(backup_folder, timestamp, model_ok, db_ok)
    cleanup_old_backups(keep=7)

    print("\n" + "="*50)
    print(f"BACKUP COMPLETE")
    print(f"Model: {manifest['model_backup']}")
    print(f"Database: {manifest['database_backup']}")
    print(f"Status: {manifest['overall_status']}")
    print("="*50)


run_backup()
