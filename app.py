from flask import Flask, render_template, request
import algos.cellular_automata as ca
# vytvořím instanci flask web aplikace
app = Flask(__name__)

def generate_map(options):
    """Generuje DnD mapu v SVG formátu dle zadaných parametrů z formuláře."""

    # TODO: 
    #   z options ziskam jedlotive parametry

    map = ca.generate_map(50, 50, floor_probability=.5, number_of_iterations=4, rock_threshold=5)
    ca.make_svg_from_map(map)



@app.route("/generate", methods=['GET', 'POST'])
def generate():
    output = request.form.to_dict()
    option = output["algoType"]

    generate_map(output)
    
    return render_template("index.html", option = option)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)