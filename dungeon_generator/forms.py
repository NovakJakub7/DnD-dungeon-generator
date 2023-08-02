import math
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, IntegerField, HiddenField, BooleanField, FloatField, PasswordField
from wtforms.validators import InputRequired, Length, NumberRange, ValidationError, Optional
from .db import get_db
from .algorithms.desc_generator import ENCOUNTER_NUMBERS, calculate_party_level

class DungeonForm(FlaskForm):
    seed = IntegerField("Dungeon Seed", validators=[InputRequired()])
    dungeon_type = SelectField("Dungeon Type", validators=[InputRequired()], choices=[("CA", "Natural Cavern Complex"), ("BSP", "Ruined/Occupied Structure")])
    dungeon_size = SelectField("Dungeon Size", validators=[InputRequired()], coerce=int, choices=[(40, "Small"), (60, "Medium"), (80, "Large"), (100, "Huge")])
    dungeon_motif = SelectField("Dungeon Motif", validators=[InputRequired()])
    number_of_players = IntegerField("Number of Players (1-10)", validators=[InputRequired(), NumberRange(1, 10)], render_kw={"placeholder": "1"})
    average_player_level = IntegerField("Average player level (1-20)", validators=[InputRequired(), NumberRange(1, 20)], render_kw={"placeholder": "1"})
    ca_rows = IntegerField("Number of Rows", validators=[Optional(), NumberRange(30, 200)], render_kw={"placeholder": "50"})
    ca_columns = IntegerField("Number of Columns", validators=[Optional(), NumberRange(30, 200)], render_kw={"placeholder": "50"})
    floor_probability = FloatField("Floor Probability in T = 0", validators=[Optional(), NumberRange(0.1, 0.9)], render_kw={"placeholder": "0.5", "step": "any"})
    rock_threshold = IntegerField("Rock Threshold", validators=[Optional(), NumberRange(1, 8)], render_kw={"placeholder": "5"})
    number_of_iterations = IntegerField("Number of Cellular Automata Iterations", validators=[Optional(), NumberRange(2, 20)], render_kw={"placeholder": "3"})
    number_of_levels = IntegerField("Number of Levels", validators=[Optional(), NumberRange(1, 20)], render_kw={"placeholder": "2"})
    bsp_rows = IntegerField("Number of Rows", validators=[Optional(), NumberRange(30, 200)], render_kw={"placeholder": "50"})
    bsp_cols = IntegerField("Number of Columns", validators=[Optional(), NumberRange(30, 200)], render_kw={"placeholder": "50"})
    bsp_min_partition_width = IntegerField("Minimal Room Width (cells)", validators=[Optional(), NumberRange(2, 50)], render_kw={"placeholder": "5"})
    bsp_min_partition_height = IntegerField("Minimal Room Height (cells)", validators=[Optional(), NumberRange(2, 50)], render_kw={"placeholder": "5"})
    number_of_floors = IntegerField("Number of Floors", validators=[Optional(), NumberRange(1, 20)], render_kw={"placeholder": "3"})
    total_treasure_value = IntegerField("Total Treasure Value (gp)", validators=[Optional(), NumberRange(min=10)], render_kw={"placeholder": "500"})
    cell_size = IntegerField("Cell Size", validators=[Optional(), NumberRange(10, 50)], render_kw={"placeholder": "10"})
    generate_dungeon = SubmitField("Generate Dungeon")
    toggled_advanced = HiddenField("Toggled Advancedd")
    more_options = BooleanField("Show More Options")

    def validate(self):
        if not super().validate():
            return False
        
        # custom check if there are suitable monsters in database for wanted encounter level
        encounter_level = calculate_party_level(self.average_player_level.data, self.number_of_players.data)
        print("EL: ",encounter_level)
        con = get_db()
        cur = con.cursor() 
        cur.execute("select challenge_rating from monsters")
        all_cr = cur.fetchall()
        a_set = set([row["challenge_rating"] for row in all_cr])
        b_set = set(ENCOUNTER_NUMBERS[encounter_level])
        print(a_set)
        print(b_set)
        if not (a_set & b_set):
            self.average_player_level.errors.append("There are not strong enough monsters in database for this level.")
            return False

        if self.more_options.data:
            if self.dungeon_type.data == "CA":
                if not self.ca_rows.data:
                    self.ca_rows.errors.append('This field is required.')
                    return False
                if not self.ca_columns.data:
                    self.ca_columns.errors.append('This field is required.')
                    return False
                if not self.floor_probability.data:
                    self.floor_probability.errors.append('This field is required.')
                    return False
                if not self.rock_threshold.data:
                    self.rock_threshold.errors.append('This field is required.')
                    return False
                if not self.number_of_iterations.data:
                    self.number_of_iterations.errors.append('This field is required.')
                    return False
                if not self.number_of_levels.data:
                    self.number_of_levels.errors.append('This field is required.')
                    return False
            elif self.dungeon_type.data == "BSP":
                if not self.bsp_rows.data:
                    self.bsp_rows.errors.append('This field is required.')
                    return False
                if not self.bsp_cols.data:
                    self.bsp_cols.errors.append('This field is required.')
                    return False
                if not self.bsp_min_partition_width.data:
                    self.bsp_min_partition_width.errors.append('This field is required.')
                    return False
                if not self.bsp_min_partition_height.data:
                    self.bsp_min_partition_height.errors.append('This field is required.')
                    return False
                if not self.number_of_floors.data:
                    self.number_of_floors.errors.append('This field is required.')
                    return False
            if not self.total_treasure_value.data:
                self.total_treasure_value.errors.append('This field is required.')
                return False
            if not self.cell_size.data:
                self.total_treasure_value.errors.append('This field is required.')
                return False

        return True
    

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired("Username is required")])
    password = PasswordField("Password", validators=[InputRequired("Password is required")])
    submit = SubmitField("Login")


class MonsterForm(FlaskForm):
    monster_name = StringField("Monster Name", validators=[InputRequired("Monster name is required"), Length(3, 30, "Monster name length should be between 3 and 30 characters")])
    monster_size = SelectField("Monster Size", validators=[InputRequired("Monster size is required")], choices=[("Fine", "Fine"), ("Diminutive", "Diminutive"), ("Tiny", "Tiny"), ("Small", "Small"), ("Medium", "Medium"), ("Large", "Large"), ("Huge", "Huge"), ("Gargantuan", "Gargantuan"), ("Colossal", "Colossal")])
    monster_type = SelectField("Monster Type", validators=[InputRequired("Monster type is required")], choices=[("Aberration", "Aberration"), ("Animal", "Animal"), ("Construct", "Construct"), ("Dragon", "Dragon"), ("Elemental", "Elemental"), ("Fey", "Fey"), ("Giant", "Giant"), ("Humanoid", "Humanoid"), ("Magical Beast", "Magical Beast"), ("Monstrous Humanoid", "Monstrous Humanoid"), ("Ooze", "Ooze"), ("Outside", "Outsider"), ("Plant", "Plant"), ("Undead", "Undead"), ("Vermin", "Vermin")])
    motif = SelectField("Monster motif", validators=[InputRequired("Monsters motif is required")], choices=[("Abandoned", "Abandoned"), ("Aberrant", "Aberrant"), ("Giant", "Giant"), ("Vermin", "Vermin"), ("Underdark", "Underdark"), ("Undead", "Undead"), ("Aquatic", "Aquatic"), ("Desert", "Desert"), ("Fire", "Fire"), ("Cold", "Cold")])
    challenge_rating = IntegerField("Challenge rating", validators=[InputRequired("Monster challenge rating is required"), NumberRange(1, 20)])
    submit = SubmitField("Add Monster")


class ItemForm(FlaskForm):
    item_name = StringField("Item Name", validators=[InputRequired("Item name is required"), Length(3, 30, "Item name length should be between 3 and 30 characters")])
    item_type = SelectField("Item Type", validators=[InputRequired("Item type is required")], choices=[("Weapon", "Weapon"), ("Shield", "Shield"), ("Armor", "Armor"), ("Ring", "Ring"), ("Rod", "Rod"), ("Scroll", "Scroll"), ("Staff", "Staff"), ("Artifact", "Artifact"), ("Wondrous Item", "Wondrous Item"), ("Cursed Item", "Cursed Item"), ("Adventuring Gear", "Adventuring Gear"), ("Tool or Skill kit", "Tool or Skill kit"), ("Clothing", "Clothing"), ("Special Item", "Special Item")])
    weight = IntegerField("Item Weight", validators=[InputRequired("Item weight is required"), NumberRange(min=1)])
    price = IntegerField("Item Price", validators=[InputRequired("Item price is required"), NumberRange(min=1)])
    submit = SubmitField("Add Item")