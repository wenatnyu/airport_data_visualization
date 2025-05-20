from app import app, db, User

def test_database():
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Try to add a test user
        try:
            test_user = User(username='testuser2')
            test_user.set_password('testpass2')
            db.session.add(test_user)
            db.session.commit()
            print("Successfully added test user!")
        except Exception as e:
            print(f"Error adding test user: {str(e)}")
            db.session.rollback()
        
        # Verify the user was added
        users = User.query.all()
        print("\nUsers in database:")
        for user in users:
            print(f"Username: {user.username}")

if __name__ == "__main__":
    test_database() 