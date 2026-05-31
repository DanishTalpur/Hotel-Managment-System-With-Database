from main import app, init_database

# Initialize the database table structure and load initial data if they don't exist
with app.app_context():
    init_database()

if __name__ == "__main__":
    app.run()
