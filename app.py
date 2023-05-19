import algos.ca as ca
import algos.bsp as bsp
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy


# vytvořím instanci flask web aplikace
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app) 

def generate_map(options):
    """Generuje DnD mapu v SVG formátu dle zadaných parametrů z formuláře."""

    # TODO: 
    #   z options ziskam jedlotive parametry

    seed = int(options["seed"])
    algoType = options["algoType"]
    size = int(options["size"])
    motif = options["motif"]

    if algoType == "ca":
        rows = size
        cols = size

        ca_cave = ca.CACave(rows, cols, seed, .5, 4, 5)
        map = ca_cave.generate_map()
        ca_cave.make_svg_from_map()
    else:
        width = size * 20
        height = size * 20

        bsp_tree = bsp.BSPTree(bsp.Rectangle(0, 0, width, height))
        bsp_tree.create_map(200, 200)
        bsp_tree.make_svg()

@app.route("/generate", methods=['GET', 'POST'])
def generate():
    options = request.form.to_dict()
    algoType = options["algoType"]

    print(options)
    generate_map(options)
    
    return render_template("dungeon.html", algoType = algoType)


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)