import dungeon_generator.algorithms.ca as ca
import dungeon_generator.algorithms.bsp as bsp
import os

def generate_map(options):
    """Generuje DnD mapu v SVG formátu dle zadaných parametrů z formuláře."""

    # TODO: 
    #   vytvořit různé velikosti map k použití na webu/downloadu

    seed = int(options["seed"])
    algoType = options["algoType"]
    size = int(options["size"])
    motif = options["motif"]

    if algoType == "ca":
        rows = size
        cols = size
        cell_size = 10

        ca_cave = ca.CACave(rows, cols, seed, .5, 4, 5)
        map = ca_cave.generate_map()
        ca_cave.make_svg_from_map(cell_size, save_path=r"C:\Users\jakub\Documents\studium\DnD-dungeon-generator\dungeon_generator\static\svg", file_name=r"map_ca.svg")
    else:
        width = size * 20
        height = size * 20

        bsp_tree = bsp.BSPTree(bsp.Rectangle(0, 0, width, height))
        bsp_tree.create_map(150, 150)
        bsp_tree.make_svg(save_path=r"C:\Users\jakub\Documents\studium\DnD-dungeon-generator\dungeon_generator\static\svg", file_name=r"map_bsp.svg")


