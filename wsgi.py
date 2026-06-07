"""
WSGI entry point for production hosts (PythonAnywhere, gunicorn, etc.).

On PythonAnywhere, point your Web app WSGI file to this module:
    from wsgi import application
"""
import os
import sys

# PythonAnywhere: uncomment and set your username + project folder if imports fail.
# PROJECT_HOME = '/home/YOUR_USERNAME/StayDesk'
# if PROJECT_HOME not in sys.path:
#     sys.path.insert(0, PROJECT_HOME)

from main import app, init_database

with app.app_context():
    init_database()

application = app
