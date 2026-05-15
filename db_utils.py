from models import db, User, SystemLog
from flask_login import current_user

def log_action(action):
    if current_user.is_authenticated:
        log = SystemLog(user_id=current_user.id, action=action)
        db.session.add(log)
        db.session.commit()

def setup_database(app):
    with app.app_context():
        db.create_all()
        # Create default admin if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Created default admin account (admin / admin123)")
