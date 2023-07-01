import dungeon_generator.generator as g
from .db import get_db
from flask import render_template, request, Blueprint

main_routes = Blueprint('main', __name__)

@main_routes.route("/generate", methods=['GET', 'POST'])
def generate():
    # vezmu data z databaze
    db_conn = get_db()

    # vezmu data z formulare
    selected_form_options = request.form.to_dict()
    
    #print(options)
    map_description = g.generate_map(selected_form_options, db_conn)
    
    return render_template("dungeon.html", map_description = map_description)

@main_routes.route("/add/item", methods=['GET', 'POST'])
def add_item():
    pass

@main_routes.route("/add/monster", methods=['GET', 'POST'])
def add_monster():
    pass

@main_routes.route("/")
def home():
    return render_template("index.html")