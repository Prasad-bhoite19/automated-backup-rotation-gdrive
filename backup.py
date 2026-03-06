import os
import json
import zipfile
import logging
import subprocess
import argparse
from datetime import datetime

CONFIG_FILE = "config.json"

logging.basicConfig(
    filename="backup.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load configuration
def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)

config = load_config()

PROJECT_NAME = config["project_name"]
SOURCE_DIR = config["source_directory"]
BACKUP_BASE = config["backup_directory"]
REMOTE = config["gdrive_remote"]
REMOTE_FOLDER = config["gdrive_folder"]
DAILY = config["retention_daily"]
WEEKLY = config["retention_weekly"]
MONTHLY = config["retention_monthly"]

WEBHOOK = config["webhook_url"]


def create_backup():

    now = datetime.now()

    year = now.strftime("%Y")
    month = now.strftime("%m")
    day = now.strftime("%d")

    timestamp = now.strftime("%Y%m%d_%H%M%S")

    backup_dir = f"{BACKUP_BASE}/{PROJECT_NAME}/{year}/{month}/{day}"
    os.makedirs(backup_dir, exist_ok=True)

    backup_name = f"{PROJECT_NAME}_{timestamp}.zip"
    backup_path = f"{backup_dir}/{backup_name}"

    with zipfile.ZipFile(backup_path, 'w') as zipf:

        for root, dirs, files in os.walk(SOURCE_DIR):
            for file in files:
                filepath = os.path.join(root, file)
                zipf.write(filepath, os.path.relpath(filepath, SOURCE_DIR))
                  logging.info(f"Backup created: {backup_path}")

    return backup_path, timestamp


def upload_to_gdrive(file_path):

    try:

        subprocess.run(
            ["rclone", "copy", file_path, f"{REMOTE}:{REMOTE_FOLDER}"],
            check=True
        )

        logging.info(f"Uploaded {file_path} to Google Drive folder {REMOTE_FOLDER}")

    except subprocess.CalledProcessError:

        logging.error("Upload failed")


def rotate_backups():

    all_backups = []

    base = f"{BACKUP_BASE}/{PROJECT_NAME}"

    for root, dirs, files in os.walk(base):
        for file in files:
                      if file.endswith(".zip"):

                try:
                    date_str = file.split("_")[1] + "_" + file.split("_")[2].replace(".zip","")
                    file_date = datetime.strptime(date_str,"%Y%m%d_%H%M%S")

                    path = os.path.join(root,file)

                    all_backups.append((file_date,path))

                except:
                    continue

    all_backups.sort(reverse=True)

    daily = []
    weekly = []
    monthly = []

    for date,path in all_backups:

        if len(daily) < DAILY:
            daily.append(path)
            continue

        if date.weekday() == 6 and len(weekly) < WEEKLY:
            weekly.append(path)
            continue
                  if date.day == 1 and len(monthly) < MONTHLY:
            monthly.append(path)
            continue

        try:
            os.remove(path)
            logging.info(f"Deleted old backup: {path}")
        except:
            pass


def send_webhook(timestamp):

    payload = json.dumps({
        "project": PROJECT_NAME,
        "date": timestamp,
        "status": "BackupSuccessful"
    })

    try:

        subprocess.run([
            "curl",
            "-X","POST",
            "-H","Content-Type: application/json",
            "-d",payload,
            WEBHOOK
        ])
              logging.info("Webhook notification sent")

    except:
        logging.error("Webhook failed")


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--no-notify",action="store_true")

    args = parser.parse_args()

    backup_path,timestamp = create_backup()

    upload_to_gdrive(backup_path)

    rotate_backups()

    if not args.no_notify:
        send_webhook(timestamp)


if __name__ == "__main__":
    main()
