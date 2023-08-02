import dungeon_generator.generator as generator
import sqlite3
from .db import get_db, db_backup
from .forms import DungeonForm, MonsterForm, ItemForm
from flask import render_template, redirect, url_for, g, request, session, Blueprint


main_routes = Blueprint('main', __name__)

@main_routes.route("/generate", methods=['GET', 'POST'])
def generate():
    logged = is_logged()
    form = DungeonForm(request.form)
    populate_motif_field(form)

    if request.method == 'POST' and form.validate():
        db_conn = get_db()
        # get form data
        form_data = form.data

        map_description = generator.generate_map(form_data, db_conn)
        
        return render_template("dungeon.html", map_description = map_description, logged = logged)
    
    return render_template("index.html", logged = logged, form = form)

@main_routes.route("/monsters", methods=['GET', 'POST'])
@main_routes.route("/monsters/<added_name>", methods=['GET', 'POST'])
def monsters(added_name = None):
    logged = is_logged()
    con = get_db()
    cur = con.cursor() 
    cur.execute("select * from monsters")
    monsters = cur.fetchall()

    form = MonsterForm()
    added = False
    if request.method == 'POST' and form.validate():
        error = None
        
        monster_name = form.monster_name.data
        monster_type = form.monster_type.data
        size = form.monster_size.data
        motif = form.motif.data
        cr = form.challenge_rating.data
        new_monster = [monster_name, size, monster_type, motif, cr]

        try:
            with con:
                con.execute("insert into monsters(monster_name, size, monster_type, motif, challenge_rating) values (?, ?, ?, ?, ?)", new_monster)
        except sqlite3.IntegrityError:
            form.monster_name.errors.append("Cannot add a monster with the same name twice.")
            error = True

        if error is None:
            db_backup()
            added = True
            return redirect(url_for('main.monsters', added_name=monster_name))

    con.close()
    return render_template("monsters.html", monsters = monsters, logged = logged, form = form, added = added, added_name = added_name)


@main_routes.route("/del/monster/<int:id>")
def delete_monster(id):
    con = get_db()
    cur = con.cursor()
    cur.execute("delete from monsters where id = ?", (id,))
    con.commit()
    con.close()
    db_backup()
    return redirect(url_for('main.monsters'))


@main_routes.route("/items", methods=['GET', 'POST'])
@main_routes.route("/items/<added_item>", methods=['GET', 'POST'])
def items(added_item = None):
    logged = is_logged()
    con = get_db()
    cur = con.cursor()
    cur.execute("select * from items")
    items = cur.fetchall()
    form = ItemForm(request.form)

    if request.method == 'POST' and form.validate():
        error = None

        item_name = form.item_name.data
        item_type = form.item_type.data
        weight = str(form.weight.data)
        weight += " lb"
        price = form.price.data
        new_item = [item_name, item_type, weight, price]

        try:
            with con:
                con.execute("insert into items(item_name, item_type, weight, price) values (?, ?, ?, ?)", new_item)
        except sqlite3.IntegrityError:
            form.item_name.errors.append("Cannot add an item with the same name twice.")
            error = True

        if error is None:
            db_backup()
            return redirect(url_for('main.items', added_item=item_name))
 
    con.close()  
    return render_template("items.html", items = items, logged = logged, form = form, added_item = added_item)
 

@main_routes.route("/del/item/<int:id>")
def delete_item(id):
    con = get_db()
    cur = con.cursor()
    cur.execute("delete from items where id = ?", (id,))
    con.commit()
    con.close()
    db_backup()
    return redirect(url_for('main.items'))


@main_routes.route("/")
def home():
    form = DungeonForm()
    form.toggled_advanced.data = False

    populate_motif_field(form)
    
    logged = is_logged()
    return render_template("index.html", logged = logged, form = form)


def is_logged():
    return False if g.user is None else True


def populate_motif_field(form):
    con = get_db()
    cur = con.cursor()
    cur.execute("select distinct motif from monsters")

    result = cur.fetchall()
    choices = [("Random", "Random")]
    for row in result:
        choices.append((row[0], row[0]))

    form.dungeon_motif.choices = choices