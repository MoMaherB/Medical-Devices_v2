from app import app, db, Device, Department, Model, User

# Create the department object
new_user = User(user_name="Peter", password='12345')
new_user_2 = User(user_name="Maher", password='12345')

with app.app_context():
    # Add and commit the department first so it gets an ID
    db.drop_all()
    db.create_all()
    db.session.add(new_user)
    db.session.add(new_user_2)


    db.session.commit()

print("Database created sucssefully!")