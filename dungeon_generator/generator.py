import dungeon_generator.algorithms.ca as ca
import dungeon_generator.algorithms.bsp as bsp
import os

def generate_map(selected_options, db_conn):
    """Generuje DnD mapu v SVG formátu dle zadaných parametrů z formuláře."""

    # TODO: 
    #   vytvořit různé velikosti map k použití na webu/downloadu

    save_path = r"C:\Users\jakub\Documents\studium\DnD-dungeon-generator\dungeon_generator\static\svg"

    seed = int(selected_options["seed"])
    algoType = selected_options["algoType"]
    motif = selected_options["motif"]
    average_player_level = int(selected_options["averagePlayerLevel"])
    number_of_players = int(selected_options["numberOfPlayers"])
    max_treasure_value = -1
    

    if algoType == "ca":
        if selected_options["toggledAdvanced"] == "True":
            rows = int(selected_options["caRows"])
            cols = int(selected_options["caCols"])
            cell_size = int(selected_options["cellSize"])
            floor_probability = float(selected_options["floorProbability"])
            number_of_iterations = int(selected_options["numberOfIterations"])
            rock_threshold = int(selected_options["rockThreshold"])
            max_treasure_value = int(selected_options["maxTreasureValue"])
        else:
            size = int(selected_options["size"])
            rows = size
            cols = size 
            cell_size = 10
            floor_probability = ca.F
            number_of_iterations = ca.N
            rock_threshold = ca.T
        
        d = ca.CADungeon(save_path, cell_size, motif, average_player_level, number_of_players, max_treasure_value, db_conn, 1)
        dungeon_description = d.generate_dungeon(rows, cols, seed, floor_probability, number_of_iterations, rock_threshold)
    else:
        if selected_options["toggledAdvanced"] == "True":
            width = int(selected_options["bspWidth"])
            height = int(selected_options["bspHeight"])
            min_partition_width = int(selected_options["bspMinPartitionWidth"])
            min_partition_height = int(selected_options["bspMinPartitionHeight"])
            max_treasure_value = int(selected_options["maxTreasureValue"])
        else:
            size = int(selected_options["size"])
            width = size * 20
            height = size * 20
            min_partition_width = 150
            min_partition_height = 150

        d = bsp.BSPDungeon(bsp.Rectangle(0, 0, width, height),seed, save_path, db_conn, 1)
        dungeon_description = d.generate_dungeon(min_partition_width, min_partition_height)

    #for level in dungeon_description:
    #        print(level)
        
    return  dungeon_description
