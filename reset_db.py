from app import app, db
from models import User

with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Recreate default admin
    admin = User(username='admin', role='admin')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("Database reset successfully.")
