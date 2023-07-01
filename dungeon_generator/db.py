import sqlite3
import os
import click
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


def init_app(app):
    app.teardown_appcontext(close_db)
    init_db()
    click.echo('Initialized the database.')