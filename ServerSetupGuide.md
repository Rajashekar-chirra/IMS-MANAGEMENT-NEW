# Inventory Management System — Full Server Setup Guide

---

## PART 1: REQUIREMENTS

### Minimum Server Specs
| Item | Minimum |
|------|---------|
| OS | Ubuntu 20.04 / 22.04 LTS (recommended) OR Windows Server 2016+ |
| RAM | 2 GB |
| Storage | 20 GB free |
| CPU | 2 Core |
| Network | Connected to office LAN |

---

## PART 2: LINUX SERVER SETUP (Ubuntu)

### Step 1 — Update the Server
```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2 — Install Python 3.11
```bash
sudo apt install -y python3.11 python3.11-venv python3-pip
python3 --version   # should show Python 3.11.x
```

### Step 3 — Install PostgreSQL
```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Step 4 — Create Database and User
```bash
sudo -u postgres psql
```
Inside the PostgreSQL prompt, type these commands one by one:
```sql
CREATE USER invuser WITH PASSWORD 'StrongPassword123';
CREATE DATABASE inventorydb OWNER invuser;
GRANT ALL PRIVILEGES ON DATABASE inventorydb TO invuser;
\q
```

### Step 5 — Upload and Extract Your Project
Copy the ZIP file to your server (via USB, FTP, or SCP), then:
```bash
sudo apt install -y unzip
unzip InventoryManagementSystem.zip -d /var/www/inventory
cd /var/www/inventory/artifacts/inventory-app
```

### Step 6 — Create Python Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
```

### Step 7 — Install Required Packages
```bash
pip install --upgrade pip
pip install flask flask-sqlalchemy flask-login psycopg2-binary openpyxl gunicorn
```

### Step 8 — Set Environment Variables
Create a file to store your settings:
```bash
sudo nano /etc/inventory.env
```
Paste the following (replace with your actual values):
```
DATABASE_URL=postgresql://invuser:StrongPassword123@localhost/inventorydb
SESSION_SECRET=change-this-to-any-long-random-text-abc123xyz
```
Save the file: Press `Ctrl+X`, then `Y`, then `Enter`

### Step 9 — Test the App First
```bash
cd /var/www/inventory/artifacts/inventory-app
source venv/bin/activate
export DATABASE_URL=postgresql://invuser:StrongPassword123@localhost/inventorydb
export SESSION_SECRET=change-this-to-any-long-random-text-abc123xyz
python run.py
```
Open a browser and go to: `http://YOUR-SERVER-IP:5000`
Login with: **admin / admin123**

If it works, press `Ctrl+C` to stop and continue to Step 10.

### Step 10 — Run as a Background Service (Auto-start)
Create a service file so the app starts automatically when the server boots:
```bash
sudo nano /etc/systemd/system/inventory.service
```
Paste this content:
```
[Unit]
Description=Inventory Management System
After=network.target postgresql.service

[Service]
User=www-data
WorkingDirectory=/var/www/inventory/artifacts/inventory-app
EnvironmentFile=/etc/inventory.env
ExecStart=/var/www/inventory/artifacts/inventory-app/venv/bin/gunicorn \
    --workers 3 \
    --bind 0.0.0.0:5000 \
    "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```
Save and close the file.

Activate the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable inventory
sudo systemctl start inventory
sudo systemctl status inventory   # should show: active (running)
```

### Step 11 — Set Up Nginx (Access Without Port Number)
Install Nginx so staff can access the app without typing `:5000`:
```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/inventory
```
Paste this content:
```
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
Activate the configuration:
```bash
sudo ln -s /etc/nginx/sites-available/inventory /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

Now staff can access the app at: `http://YOUR-SERVER-IP` (no port number needed)

---

## PART 3: WINDOWS SERVER SETUP

### Step 1 — Install Python 3.11
- Download from: https://www.python.org/downloads/
- During install: CHECK the box **"Add Python to PATH"**

### Step 2 — Install PostgreSQL
- Download from: https://www.postgresql.org/download/windows/
- During install: set a password for the `postgres` user (remember it)
- Port: leave as `5432`

### Step 3 — Create Database
Open **pgAdmin** (installed with PostgreSQL):
1. Right-click **Databases** → **Create** → **Database**
2. Name it: `inventorydb`
3. Owner: `postgres`

### Step 4 — Extract Project Files
Extract the ZIP to: `C:\inventory\`

### Step 5 — Install Python Packages
Open **Command Prompt as Administrator**:
```cmd
cd C:\inventory\artifacts\inventory-app
pip install flask flask-sqlalchemy flask-login psycopg2-binary openpyxl gunicorn waitress
```

### Step 6 — Create a Startup Script
Create a file: `C:\inventory\start.bat`
```bat
@echo off
set DATABASE_URL=postgresql://postgres:YourPassword@localhost/inventorydb
set SESSION_SECRET=change-this-to-any-long-random-text
cd C:\inventory\artifacts\inventory-app
python run.py
```

### Step 7 — Run the App
Double-click `start.bat`
Open browser: `http://localhost:5000` or `http://YOUR-SERVER-IP:5000`

### Step 8 — Auto-start on Windows Boot (Optional)
To run automatically when the server starts:
- Press `Win + R`, type `shell:startup`
- Copy a shortcut of `start.bat` into that folder

---

## PART 4: OPEN FIREWALL (Both Linux & Windows)

### Linux (Ubuntu)
```bash
sudo ufw allow 80/tcp
sudo ufw allow 5000/tcp
sudo ufw enable
```

### Windows
1. Open **Windows Defender Firewall**
2. Click **Inbound Rules** → **New Rule**
3. Select **Port** → TCP → enter `5000` → Allow → Save

---

## PART 5: HOW STAFF ACCESS THE APP

Once running, staff on the same office network open any browser and go to:

| Setup | Address to type |
|-------|----------------|
| Linux with Nginx | `http://192.168.X.X` |
| Linux without Nginx | `http://192.168.X.X:5000` |
| Windows | `http://192.168.X.X:5000` |

Replace `192.168.X.X` with your actual server's IP address.

To find your server IP on Linux:
```bash
hostname -I
```
On Windows:
```cmd
ipconfig
```

---

## PART 6: DEFAULT LOGIN

| Username | Password |
|----------|----------|
| admin | admin123 |

**Change this password immediately after first login** through the app's user settings.

---

## PART 7: REGULAR BACKUP (Recommended)

### Database Backup (Linux)
```bash
pg_dump -U invuser inventorydb > /home/backup/inventory_$(date +%F).sql
```
Run this weekly. Store backups on a separate drive or USB.

### Database Backup (Windows)
In pgAdmin: Right-click database → **Backup** → Save as `.sql` file.

---

## PART 8: TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Can't connect to database | Check DATABASE_URL, confirm PostgreSQL is running |
| App not starting | Run `python run.py` manually to see error |
| Port 5000 not accessible | Check firewall settings |
| Staff can't open the link | Confirm they're on the same network, check server IP |
| Forgot admin password | Run: `python reset_password.py` (see below) |

### Reset Admin Password
```bash
cd /var/www/inventory/artifacts/inventory-app
source venv/bin/activate
python3 -c "
from app import create_app, db
from models import User
app = create_app()
with app.app_context():
    u = User.query.filter_by(username='admin').first()
    u.set_password('NewPassword123')
    db.session.commit()
    print('Password reset done')
"
```

---

## PART 9: SUMMARY CHECKLIST

- [ ] Server OS installed (Ubuntu 22.04 recommended)
- [ ] Python 3.11 installed
- [ ] PostgreSQL installed and running
- [ ] Database `inventorydb` created
- [ ] Project files extracted to `/var/www/inventory`
- [ ] Python packages installed in virtual environment
- [ ] Environment variables set (DATABASE_URL, SESSION_SECRET)
- [ ] App tested manually at `http://SERVER-IP:5000`
- [ ] Systemd service created (auto-start on boot)
- [ ] Nginx configured (optional, removes port number)
- [ ] Firewall opened for port 80 / 5000
- [ ] Staff tested access from their computers
- [ ] Admin password changed from default

---

*Guide prepared for: Government/Office Inventory Management System*
*Stack: Python 3.11 + Flask + PostgreSQL + Bootstrap 5*
