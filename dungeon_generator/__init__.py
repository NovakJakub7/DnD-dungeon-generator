import os
from flask import Flask
from . import db

def create_app():
   # vytvořím instanci flask web aplikace
    app = Flask(__name__)

    # konfigurace
    app.config['SECRET_KEY'] = 'dev'
       
    db_path = os.path.join(app.instance_path, 'database.sqlite')

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Check if the database file exists, and create it if necessary
    if not os.path.exists(db_path):
        open(db_path, 'a').close()

    from .routes import main_routes
    app.register_blueprint(main_routes)

    from .db import init_app
    with app.app_context():
        init_app(app)

    return app