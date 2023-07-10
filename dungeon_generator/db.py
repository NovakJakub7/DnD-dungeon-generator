import sqlite3
import os
import click
import shutil
from werkzeug.security import generate_password_hash
from flask import current_app, g


def get_db():
    if 'db' not in g:
        db_path = os.path.join(current_app.instance_path, 'database.sqlite')
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


def db_backup():
    db_path = os.path.join(current_app.instance_path, 'database.sqlite')
    backup_path = os.path.join(current_app.instance_path, 'database_backup.sqlite')
    # Create backup
    shutil.copyfile(db_path, backup_path)
    click.echo("Database backup created.")


def init_app(app):
    app.teardown_appcontext(close_db)
    db_path = os.path.join(app.instance_path, 'database.sqlite')
    backup_path = os.path.join(app.instance_path, 'database_backup.sqlite')

    # Check if backup file exists
    if os.path.exists(backup_path):
        # Restore from backup
        shutil.copyfile(backup_path, db_path)
        click.echo("Database restored from backup.")
    else:
        init_db()
        click.echo('Initialized the database.')
        
        db = get_db()
        cur = db.cursor()
        username = "admin"
        password = "admin"
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, generate_password_hash(password)))
        db.commit()
        click.echo("Admin user created.")
        cur.close()
        db.close()

        # Create backup
        shutil.copyfile(db_path, backup_path)
        click.echo("Database backup created.")

    click.echo("App initialized")
    
    