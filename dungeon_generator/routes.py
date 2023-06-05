import dungeon_generator.generator as g
from flask import render_template, request, Blueprint

main_routes = Blueprint('main', __name__)

@main_routes.route("/generate", methods=['GET', 'POST'])
def generate():
    options = request.form.to_dict()
    algoType = options["algoType"]

    print(options)
    g.generate_map(options)
    
    return render_template("dungeon.html", algoType = algoType)


@main_routes.route("/")
def home():
    return render_template("index.html")