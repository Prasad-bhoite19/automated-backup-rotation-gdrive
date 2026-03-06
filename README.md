# 🚀 Automated Backup System with Google Drive & Webhook Notifications

![Python](https://img.shields.io/badge/Python-3.x-blue)
![AWS](https://img.shields.io/badge/AWS-EC2-orange)
![Linux](https://img.shields.io/badge/Linux-Ubuntu-green)
![Rclone](https://img.shields.io/badge/Rclone-Cloud%20Sync-purple)

---

# 📌 Project Overview

The **Automated Backup System** is a cloud automation project that performs automatic backups from an **AWS EC2 Ubuntu server** to **Google Drive** using **Rclone**.

The system is designed to:

• Automate backup tasks  
• Store backups securely in cloud storage  
• Send real-time notifications using Webhooks  
• Run automatically using Cron Jobs  

This project demonstrates **DevOps automation, cloud integration, and infrastructure reliability practices.**

---

# 🎯 Project Objectives

- Automate server file backups
- Store backups in Google Drive
- Implement real-time monitoring
- Reduce manual intervention
- Implement DevOps automation
- Improve system reliability

---

# 🧰 Technologies Used

| Technology | Purpose |
|-----------|--------|
| AWS EC2 | Cloud server |
| Ubuntu Linux | Operating system |
| Python | Automation script |
| Rclone | Cloud storage sync |
| Google Drive | Backup storage |
| Webhook.site | Notification monitoring |
| Cron Jobs | Scheduling automation |
| GitHub | Version control |

---

# 🏗️ System Architecture

```mermaid
flowchart LR

A[Server Files] --> B[Python Backup Script]
B --> C[Rclone Sync]
C --> D[Google Drive]

B --> E[Webhook Notification]
E --> F[Webhook Dashboard]

G[Cron Job Scheduler] --> B
```

---

# ☁️ Architecture Workflow

```mermaid
sequenceDiagram

participant Server
participant Script
participant Rclone
participant Drive
participant Webhook

Server->>Script: Trigger Backup
Script->>Rclone: Execute Sync
Rclone->>Drive: Upload Backup
Script->>Webhook: Send Notification
Webhook->>User: Show Backup Status
```

---

# 📂 Project Folder Structure

```
BackupProject
│
├── Projects
└── Myproject
├── backup.py
├── config.json
├── backup.log
└── backups

```

---

# ⚙️ Prerequisites

Before starting the project install the following:

- AWS Account
- Ubuntu EC2 Instance
- Python3
- Rclone
- Google Drive account
- Webhook.site URL

---

# 🚀 Project Setup Steps

---

## 1️⃣ Launch EC2 Instance

Login to AWS Console

Create **Ubuntu EC2 Instance**

Connect using SSH

```
ssh ubuntu@your-ec2-public-ip
```

---

## 2️⃣ Update System

```
sudo apt update
sudo apt upgrade -y
```

---

## 3️⃣ Install Python

```
sudo apt install python3 -y
```

Verify installation

```
python3 --version
```

---

## 4️⃣ Install Rclone

```
curl https://rclone.org/install.sh | sudo bash
```

Verify installation

```
rclone version
```

---

## 5️⃣ Configure Google Drive

Run

```
rclone config
```

Choose

```
n → new remote
name → gdrive
storage → drive
```

Complete authentication.

Test connection

```
rclone ls gdrive:
```

---

# 📄 Project Configuration Files

---

# config.json

```json
{
  "project_name": "MyProject",
  "source_directory": "/home/ubuntu/BackupProject/Projects",
  "backup_directory": "/home/ubuntu/backups",
  "gdrive_remote": "gdrive",
  "gdrive_folder": "BackupFolderName",

  "retention_daily": 7,
  "retention_weekly": 4,
  "retention_monthly": 3,

  "webhook_url": "https://webhook.site/284d5480-874e-4566-ab28-037b97515273"
}
```

---

# backup.py

```python

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

```

---

# ⏰ Cron Job Automation

Open crontab

```
crontab -e
```

Add the following job

```
0 2 * * * * python3 /home/ubuntu/BackupProject/backup.py
```

This will run the backup **every hour automatically**.

---

# 🔔 Webhook Notification Flow

```mermaid
graph TD

BackupScript --> WebhookURL
WebhookURL --> WebhookSiteDashboard
WebhookSiteDashboard --> UserNotification
```

---

# 🖼️ Expected Screenshots

Add these screenshots to your documentation.

1. EC2 Instance Running
2. SSH Connection to Server
3. Rclone Installation
4. Google Drive Configuration
5. Project Folder Structure
6. Running Backup Script
7. Files Uploaded to Google Drive
8. Webhook Notification Received
9. Cron Job Configuration

---

# ⚠️ Issues Faced and Solutions

---

## Issue 1: Python Command Not Found

Error

```
python: command not found
```

Solution

Use

```
python3 backup.py
```

---

## Issue 2: Rclone Command Not Found

Error

```
rclone: command not found
```

Solution

Reinstall Rclone

```
curl https://rclone.org/install.sh | sudo bash
```

---

## Issue 3: Google Drive Not Syncing

Solution

Reconfigure Rclone

```
rclone config
```

---

# 📊 Project Benefits

✔ Fully automated backup system  
✔ Secure cloud storage integration  
✔ Real-time monitoring  
✔ DevOps automation implementation  
✔ Disaster recovery ready  

---

# 🔐 Security Best Practices

- Do not upload `config.json` publicly
- Restrict Google Drive access
- Protect webhook URL
- Use proper IAM policies

---

# 🔮 Future Improvements

- Add AWS S3 backup
- Integrate Slack notifications
- Add logging dashboard
- Implement Docker container
- Add monitoring using Prometheus

---

# 👨‍💻 Author

**Prasad Bhoite**  
Cloud & DevOps Enthusiast

## 📩 Connect With Me :-

If you’d like to collaborate, discuss projects, or just say hello — feel free to reach out!  

### 🔗 Social & Professional Links
- 🌐 [Portfolio Website](https://prasad-bhoite19.github.io/prasad-portfolio/)  
- 💼 [LinkedIn](http://linkedin.com/in/prasad-bhoite-a38a64223)  
- 🐙 [GitHub](https://github.com/Prasad-bhoite19)  
- ✉️ [Email](prasadsb2002@gmail.com)  

---

# ⭐ Support

If you like this project

⭐ Star the repository  
🍴 Fork the repository  
📢 Share with others  

---

# 📜 License

This project is created for **educational and learning purposes**.

---
