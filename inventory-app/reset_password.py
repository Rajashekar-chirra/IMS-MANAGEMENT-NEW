"""
Reset the admin password.

Usage:
    python reset_password.py
    python reset_password.py NewPasswordHere

If no password is given, it resets the 'admin' account back to 'admin123'.
"""
import sys
from app import create_app, db
from models import User

new_password = sys.argv[1] if len(sys.argv) > 1 else 'admin123'

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if not user:
        print("No 'admin' user found in the database.")
        sys.exit(1)
    user.set_password(new_password)
    db.session.commit()
    print(f"Admin password has been reset to: {new_password}")
