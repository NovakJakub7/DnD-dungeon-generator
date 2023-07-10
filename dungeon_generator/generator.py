import dungeon_generator.algorithms.ca as ca
import dungeon_generator.algorithms.bsp as bsp
import os

def generate_map(selected_options, db_conn):
    """Generuje DnD mapu v SVG formátu dle zadaných parametrů z formuláře."""

    # TODO: 
    #   vytvořit různé velikosti map k použití na webu/downloadu

    save_path = r"C:\Users\jakub\Documents\studium\DnD-dungeon-generator\dungeon_generator\static\svg"

    seed = int(selected_options["seed"])
    dungeon_type = selected_options["dungeon_type"]
    dungeon_motif = selected_options["dungeon_motif"]
    average_player_level = int(selected_options["average_player_level"])
    number_of_players = int(selected_options["number_of_players"])
    max_treasure_value = -1
    

    if dungeon_type == "CA":
        if selected_options["toggled_advanced"] == "True":
            rows = int(selected_options["ca_rows"])
            cols = int(selected_options["ca_columns"])
            cell_size = int(selected_options["cell_size"])
            floor_probability = float(selected_options["floor_probability"])
            number_of_iterations = int(selected_options["number_of_iterations"])
            rock_threshold = int(selected_options["rock_threshold"])
            max_treasure_value = int(selected_options["max_treasure_value"])
            number_of_levels = int(selected_options["number_of_levels"])
        else:
            dungeon_size = int(selected_options["dungeon_size"])
            rows = dungeon_size
            cols = dungeon_size 
            cell_size = 15
            floor_probability = ca.F
            number_of_iterations = ca.N
            rock_threshold = ca.T
            number_of_levels = 1
        
        d = ca.CADungeon(save_path, cell_size, dungeon_motif, average_player_level, number_of_players, max_treasure_value, db_conn, number_of_levels)
        dungeon_description = d.generate_dungeon(rows, cols, seed, floor_probability, number_of_iterations, rock_threshold)
    else:
        if selected_options["toggled_advanced"] == "True":
            cell_size = int(selected_options["cell_size"])
            width = int(selected_options["bsp_cols"]) * cell_size
            height = int(selected_options["bsp_rows"]) * cell_size
            min_partition_width = int(selected_options["bsp_min_partition_width"]) * cell_size
            min_partition_height = int(selected_options["bsp_min_partition_height"]) * cell_size
            max_treasure_value = int(selected_options["max_treasure_value"])
            number_of_floors = int(selected_options["number_of_floors"])          
        else:
            cell_size = 15
            size = int(selected_options["dungeon_size"])
            width = size * cell_size
            height = size * cell_size
            min_partition_width = 5 * cell_size
            min_partition_height = 5 * cell_size
            number_of_floors = 1       

        d = bsp.BSPDungeon(bsp.Rectangle(0, 0, width, height),seed, dungeon_motif, cell_size, average_player_level,number_of_players,max_treasure_value, save_path, db_conn, number_of_floors)
        dungeon_description = d.generate_dungeon(min_partition_width, min_partition_height)

    #for level in dungeon_description:
    #        print(level)
        
    return  dungeon_description
