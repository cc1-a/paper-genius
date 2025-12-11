from app import app, db, users
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    
    admin_email = "genius.paperss@gmail.com"
    existing_admin = db.session.execute(db.select(users).filter_by(email=admin_email)).scalar_one_or_none()
    
    if not existing_admin:
        hashed_pw = generate_password_hash("amodh2006")
        new_admin = users(
            name="Amodh",
            email=admin_email,
            password=hashed_pw,
            school="Paper Genius HQ",
            level="Admin",
            number="94766226039",
            address="Kottawa",
            town="Colombo"
        )
        db.session.add(new_admin)
        db.session.commit()
        print("Success! Database created and Admin User added.")
    else:
        print("Admin already exists.")