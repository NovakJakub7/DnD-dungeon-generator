import random
import svgwrite
import pathlib
import math
import os
from svglib.svglib import svg2rlg
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from .desc_generator import DescriptionGenerator, calculate_party_level, level_description_to_text, ENCOUNTER_NUMBERS

# needed for pyvips library functionality
current_directory = pathlib.Path.cwd()
dlls_folder = current_directory.joinpath("dungeon_generator", "dependencies", "vips-dev-8.14", "bin")

os.add_dll_directory(dlls_folder)
os.environ['PATH'] += os.pathsep + str(dlls_folder)

import pyvips

DISCARD_BY_RATIO = True
H_RATIO = 0.45
W_RATIO = 0.45

class BSPDungeon:
    def __init__(self, bounds, seed, motif: str, cell_size: int,  average_player_level: int, number_of_players: int, total_treasure_value: int, save_path: str, db_conn = None, number_of_floors: int = 1) -> None:
        self.bounds = bounds
        self.seed = seed
        self.db_conn = db_conn
        self.save_path = save_path
        self.number_of_floors = number_of_floors
        self.motif = motif
        self.cell_size = cell_size
        self.total_treasure_value = total_treasure_value
        self.average_player_level = average_player_level
        self.number_of_players = number_of_players


    def generate_dungeon(self, min_partition_width: int, min_partition_height: int) -> list:
        """Function uses Binary Space Partitioning to generate one or more dungeons with descriptions and saves them as SVG images.

        Args:
            min_partition_width (int): Minimum width of partitioned subspace
            min_partition_height (int): Minimum height of partitioned subspace

        Returns:
            list: dungeon description
        """
        package_path = pathlib.Path.cwd()
        image_dir = package_path.joinpath("dungeon_generator", "static","images")

        floors = []
        dungeon_description = []

        for i in range(0, self.number_of_floors):
            file_name = f"map_bsp_{i}.svg"
            pdf_file_name = f"map_bsp_{i}.pdf"
            png_file_name = f"map_bsp_{i}.png"
            if i > 0:
                bsp_tree = BSPTree(self.bounds, self.seed + i, self.cell_size, upper_floor=floors[i - 1], floor_depth=i + 1, number_of_floors=self.number_of_floors)
            else:
                bsp_tree = BSPTree(self.bounds, self.seed, self.cell_size, upper_floor=None, floor_depth=i + 1, number_of_floors=self.number_of_floors)
            floors.append(bsp_tree.create_map(min_partition_width, min_partition_height))
            desc = bsp_tree.place_monsters_items(self.db_conn, self.average_player_level, self.number_of_players, self.total_treasure_value, self.motif)
            bsp_tree.make_svg(self.save_path, file_name)

            level_description = {'level_id': i, 'desc_list': desc, 'svg_file': file_name, 'pdf_file': pdf_file_name}
            dungeon_description.append(level_description)

            self.convert_svg_to_pdf(self.save_path.joinpath(file_name), image_dir.joinpath(pdf_file_name), image_dir.joinpath(png_file_name), (self.bounds.width), (self.bounds.height), level_description)   


        return  dungeon_description
    

    def convert_svg_to_pdf(self, input_svg, output_pdf, png_img, width, height, level_desc) -> None:
        """Convert svg map and map description to pdf using reportlab library.

        Args:
            input_svg (Path): SVG file path
            output_pdf (Path): Output PDF path
            width (Int): SVG width
            height (Int): SVG height
            level_desc (list): Level description
        """
        
        image = pyvips.Image.new_from_file(input_svg)
        image.write_to_file(png_img)

        # Create a new PDF canvas
        size = (width + 100, height + 100)
        c = canvas.Canvas(str(output_pdf), pagesize=landscape(size))

        # Load the SVG image using svglib
        #drawing = svg2rlg(input_svg)

        # Set the position and scale of the SVG image on the canvas
        x = (size[0] - width) / 2
        y = size[1] - height - 50

        # Draw the SVG image on the canvas
        c.drawImage(png_img, x, y)

        # Make new page
        c.showPage()

        text = level_description_to_text(level_desc, "BSP")
       
        # Set the position for the text
        text_x = 50
        text_y = size[1] - 50

        # Draw text
        text_object = c.beginText(text_x, text_y)
        text_object.setFont("Helvetica", 12)
        for line in text.split('\n'):
            text_object.textLine(line)
        c.drawText(text_object)

        # Save the canvas to the PDF file
        c.save()

        # Remove the png
        os.remove(png_img)


class BSPTree:
    def __init__(self, bounds, seed: int, cell_size: int, upper_floor = None, floor_depth: int = 0, number_of_floors: int = 0) -> None:
        self.root = BSPNode(bounds)
        self.min_partition_width = 0
        self.min_partition_height = 0
        self.upper_floor = upper_floor
        self.entry = None
        self.entry_direction = ""
        self.exit = None
        self.exit_direction = ""
        self.entry_size = 0
        self.floor_depth = floor_depth
        self.number_of_floors = number_of_floors
        self.svg_name = ""
        self.cell_size = cell_size
        self.seed = seed
        random.seed(seed)
        

    def create_map(self, min_partition_width: int, min_partition_height: int) -> None:
        """Function creates a representation of a dungeon map.

        Args:
            min_partition_width (int):  Minimum width of partitioned subspace
            min_partition_height (int):  Minimum height of partitioned subspace

        Returns:
            BSPTree: self
        """

        self.min_partition_width = min_partition_width
        self.min_partition_height = min_partition_height

        min_room_width = math.ceil(min_partition_width / 100 * 80 / self.cell_size) * self.cell_size
        min_room_height = math.ceil(min_partition_height / 100 * 80 / self.cell_size) * self.cell_size

        self.partition(min_partition_width + 2 * self.cell_size, min_partition_height + 2 * self.cell_size, self.cell_size)
        self.create_rooms(min_room_width, min_room_height, self.cell_size)
        self.create_corridors()
        self.place_entry_exit()

        return self


    def partition(self, min_width: int, min_height: int, cell_size: int) -> None:
        """Apply space partitioning on root node.

        Args:
            min_width (int): Minimum width of partitioned subspace
            min_height (int): Minimum height of partitioned subspace
            cell_size (int): Size of the cells in map pattern
        """

        self.root.partition(min_width, min_height, cell_size)
        

    def get_leaf_nodes(self) -> list:
        """Returns list of leaf nodes."""
        return self.root.get_leaf_nodes()


    def create_rooms(self, min_width: int, min_height: int, cell_size: int) -> None:
        """Creates a room for every leaf node in tree.

        Args:
            min_width (int): Minimum room width
            min_height (int): Minimum room height
            cell_size (int): Size of the cells in map pattern
        """
        for node in self.get_leaf_nodes():
            node.create_room(min_width, min_height, cell_size)


    def create_corridors(self) -> None:
        """Creates corridors between rooms of sibling nodes."""
        self.root.create_corridors(self.cell_size)


    def get_rooms(self) -> list:
        """Returns a list of all Rooms"""
        nodes = self.get_leaf_nodes()
        rooms = []

        for node in nodes:
            rooms.append(node.room)

        return rooms
    

    def get_corridors(self) -> list:
        """Returns a list of all corridors"""
        root = self.root
        corridors = root.get_corridors()

        return corridors
    

    def place_entry_exit(self) -> None:
        """Place entry and exit points into the map."""
        rooms = self.get_rooms()   
        directions = ["left", "right", "top", "bottom"]
        entry_direction = ""
        self.entry_size = math.ceil(self.min_partition_width / 100 * 25)

        # ENTRY
        # no upper floor, make random entry based on direction
        if self.upper_floor is None:
            entry_direction = random.choice(directions)
            entry_room, entry_point  = self.make_random_door(rooms, entry_direction)
            self.entry_direction = entry_direction
            self.entry = entry_point         
        else: # make entry (staircase) based on upper floor exit
            upper_floor_exit = self.upper_floor.exit           
            entry_room = self.find_closest_room(upper_floor_exit, rooms)
            staircase, entry_direction = self.make_staircase(entry_room)
            self.entry_direction = entry_direction
            self.entry = staircase

        #EXIT
        possible_exit_rooms = rooms
        possible_exit_rooms.remove(entry_room)
        # if there is just one floor or there are no more floors make exit in random room
        if self.number_of_floors == 0 or self.floor_depth == self.number_of_floors:
            # choose direction that is not the entry direction
            exit_directions = directions
            if entry_direction != "":
                exit_directions.remove(entry_direction)
            exit_direction = random.choice(exit_directions)
            exit_room, exit_point = self.make_random_door(possible_exit_rooms, exit_direction)  
            self.exit_direction = exit_direction
            self.exit = exit_point     
        else: # otherwise make exit staircase in random room
            exit_room = random.choice(possible_exit_rooms) 
            staircase, exit_direction = self.make_staircase(exit_room)
            self.exit_direction = exit_direction
            self.exit = staircase


    def place_monsters_items(self, db_conn, average_player_level: int, number_of_players: int, total_treasure_value: int, motif: str) -> list:
        """Function creates dictionary describing item and monster placement inside the dungeon.

        Args:
            db_conn (Connection): Database connection
            average_player_level (int): Average player level
            number_of_players (int): Number of players
            total_treasure_value (int): Total treasure value
            motif (str): Cave motif

        Returns:
            list: Cave descriptions
        """
        encounter_level = calculate_party_level(average_player_level, number_of_players)
        if encounter_level == 0:
            encounter_level = 1
        desc_generator = DescriptionGenerator(encounter_level, total_treasure_value)

        available_motives = []
        motif_found = False
        if motif == "Random":
            motives = self.query_db(db_conn, 'select distinct motif from monsters')
            for motive in motives:
                available_motives.append(motive['motif'])
            while not motif_found:
                motif = random.choice(available_motives)
                ratings = self.query_db(db_conn, 'select challenge_rating from monsters where motif = ?', [motif])
                rating_set = set([row["challenge_rating"] for row in ratings])
                encounter_set = set(ENCOUNTER_NUMBERS[encounter_level])
                if len(rating_set.intersection(encounter_set)) != 0:
                    motif_found = True
                else:
                    available_motives.pop(available_motives.index(motif))
                    
        rooms = self.get_rooms()
        room_sizes = []
        number_of_rooms = len(rooms)
        smaller_monsters_sizes = ["Fine", "Diminutive", "Tiny", "Small", "Medium"]
        larger_monsters_sizes = ["Medium", "Large", "Huge", "Gargantuan", "Colossal"]
        smaller_monsters = self.query_db(db_conn, "select * from monsters where size in ({}) and challenge_rating <= ? and motif = ?".format(','.join(['?'] * len(smaller_monsters_sizes))), smaller_monsters_sizes + [encounter_level, motif])
        larger_monsters = self.query_db(db_conn, "select * from monsters where size in ({}) and challenge_rating <= ? and motif = ?".format(','.join(['?'] * len(larger_monsters_sizes))), larger_monsters_sizes + [encounter_level, motif])
        items = self.query_db(db_conn, 'select * from items')
        dungeon_description = []

        for room in rooms:
            room_sizes.append(room.width * room.height)
        room_sizes.sort(reverse=True)
        
        # decide large and small rooms
        if number_of_rooms < 10:
            large_rooms_index = 1
            small_rooms_index = number_of_rooms - 2
        elif number_of_rooms >= 10 and number_of_rooms < 20:
            large_rooms_index = 3
            small_rooms_index = number_of_rooms - 3
        else:
            large_rooms_index = 4
            small_rooms_index = number_of_rooms - 4

        large_size = room_sizes[large_rooms_index]
        small_size = room_sizes[small_rooms_index] 
        
        # make descriptions based on room size
        for room in rooms:
            room_size = room.width * room.height
            if room_size >= large_size: # large rooms, large monsters and treasure
                if larger_monsters:
                    monster_description = desc_generator.generate_monster_description(larger_monsters)
                else:
                    monster_description = desc_generator.generate_monster_description(smaller_monsters)
                treasure_description = desc_generator.generate_treasure_description(items)
                dungeon_description.append({'cave_id': rooms.index(room), 'monster_desc': monster_description, 'treasure': treasure_description})    
            elif room_size < large_size and room_size > small_size: # medium rooms, small monsters
                monster_description = {}
                if random.random() < .4:
                    if smaller_monsters:
                        monster_description = desc_generator.generate_monster_description(smaller_monsters)
                dungeon_description.append({'cave_id': rooms.index(room), 'monster_desc': monster_description, 'treasure': {}})
            else: # small rooms, treasure
                treasure_description = desc_generator.generate_treasure_description(items)
                dungeon_description.append({'cave_id': rooms.index(room), 'monster_desc': {}, 'treasure': treasure_description})

        dungeon_description = sorted(dungeon_description, key=lambda x: x['cave_id'])

        # add rest of treasure to random room
        if desc_generator.rest_of_value > 0:
            random_desc = random.choice(dungeon_description)
            while not random_desc["treasure"]:
                random_desc = random.choice(dungeon_description)
            random_desc["treasure"]["gp"] += desc_generator.rest_of_value

        return dungeon_description


    def query_db(self, db_conn, query, args=(), one=False):
        """Query databse and return the result."""
        cur = db_conn.cursor().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv


    def is_room_inside(self, outer_rect, inner_rect) -> bool:
        """Return True if room is inside another room, otherwise return False.

        Args:
            outer_rect (Rectangle): Outer rectangle representing room
            inner_rect (Rectangle): Inner rectangle representing rom

        Returns:
            bool: Is inner room inside outer room
        """
        if (
            outer_rect.left <= inner_rect.left and
            outer_rect.top <= inner_rect.top and
            outer_rect.right >= inner_rect.right and
            outer_rect.bottom >= inner_rect.bottom
        ):
            return True

        return False


    def find_closest_room(self, target_room, rooms):
        """Return the closest room to another room."""
        closest_room = None
        closest_distance = float('inf')
        target_room_center_x, target_room_center_y = target_room.center()

        for room in rooms:
            room_center_x, room_center_y = room.center()
            distance = (target_room_center_x - room_center_x) ** 2 + (target_room_center_y - room_center_y) ** 2
            if distance < closest_distance:
                closest_distance = distance
                closest_room = room

        return closest_room


    def make_staircase(self, room) -> tuple:
        """Function creates a staircase in room.

        Args:
            room (Rectangle): Room

        Returns:
            tuple: Staircase and direction
        """
        direction = random.choice(["left", "right", "top", "bottom"])
        staircase = Rectangle(0,0,0,0)
        staircase_width = self.cell_size * 2
        staircase_heigth = self.cell_size *2
        if direction == "left":
            if random.random() < .5: # from top
                staircase = Rectangle(room.left, room.top, staircase_width, staircase_heigth)
            else: # from bottom
                staircase = Rectangle(room.left, room.bottom - staircase_heigth, staircase_width, staircase_heigth)
        elif direction == "right":
            if random.random() < .5: # from top
                staircase = Rectangle(room.right - staircase_width, room.top, staircase_width, staircase_heigth)
            else: # from bottom
                staircase = Rectangle(room.right - staircase_width, room.bottom - staircase_heigth, staircase_width, staircase_heigth)
        elif direction == "top":
            if random.random() < .5: # from left
                staircase = Rectangle(room.left, room.top, staircase_width, staircase_heigth)
            else: # from right
                staircase = Rectangle(room.right - staircase_width, room.top, staircase_width, staircase_heigth)
        elif direction == "bottom":
            if random.random() < .5: # from left
                staircase = Rectangle(room.left, room.bottom - self.cell_size, staircase_width, staircase_heigth)
            else: # from right
                staircase = Rectangle(room.right - staircase_width, room.bottom - self.cell_size, staircase_width, staircase_heigth)

        corridors = self.get_corridors()

        if self.is_corridor_through_rect(corridors, staircase):
            #print("CORRIDOR IS THROUGH")
            return self.make_staircase(room)
        else:
            return (staircase, direction)
    

    def is_corridor_through_rect(self, corridors, room) -> bool:
        """Return True if corridor passes through rectangle, otherwise false."""
        for rect in corridors:
            if (
                rect.right > room.left and        # Right edge of rect is to the right of room's left edge
                rect.left < room.right and        # Left edge of rect is to the left of room's right edge
                rect.bottom > room.top and        # Bottom edge of rect is below room's top edge
                rect.top < room.bottom            # Top edge of rect is above room's bottom edge
            ):
                return True
        return False


    def make_random_door(self, rooms: list, direction: str) -> tuple:
        """Function creates door in given direction and returns the door room and door as tuple.

        Args:
            rooms (list): List of available rooms
            direction (str): Direction of the door

        Returns:
            tuple: Room with doors and door coordinates
        """
        door_point = ()
        if direction == "left":
            door_room = min(rooms, key=lambda x: x.left)
            door_point = (door_room.left, random.randrange(door_room.top + self.cell_size, door_room.bottom - self.cell_size + 1, self.cell_size))
        elif direction == "right":
            door_room = max(rooms, key=lambda x: x.right)
            door_point = (door_room.right, random.randrange(door_room.top + self.cell_size, door_room.bottom - self.cell_size + 1, self.cell_size))
        elif direction == "top":
            door_room = min(rooms, key=lambda x: x.top)
            door_point = (random.randrange(door_room.left + self.cell_size, door_room.right - self.cell_size + 1, self.cell_size), door_room.top)
        else: # bottom
            door_room = max(rooms, key=lambda x: x.bottom)
            door_point = (random.randrange(door_room.left + self.cell_size, door_room.right - self.cell_size + 1, self.cell_size), door_room.bottom)
        return (door_room, door_point)

    def make_svg(self, save_path: str, file_name: str) -> None:
        """Function generates SVG image from BSPTree and saves it to path under the file name.

        Args:
            save_path (str): Path in file directory where the SVG will be saved
            file_name (str): SVG file name
        """
        file_path = save_path.joinpath(file_name)

        self.svg_name = file_name

        canvas_width = '{}px'.format(self.root.bounds.width)
        canvas_height = '{}px'.format(self.root.bounds.height)

        # Create a Drawing object and specify the file path
        dwg = svgwrite.Drawing(file_path, profile='full', size=(canvas_width, canvas_height))

        # black map background
        map = dwg.add(dwg.rect((self.root.bounds.left, self.root.bounds.top), (self.root.bounds.width, self.root.bounds.height)))
        map.fill('black')
        map.stroke('black', width=2)

        room_numbers = []
        room_numbers = self.root.draw_rooms(dwg, self.cell_size)
        self.root.draw_corridors(dwg, self.cell_size)
        self.draw_misc(dwg)
        
        for number in room_numbers:
            id = number["id"]
            x = number["insert_x"]
            y = number["insert_y"]
            text = dwg.text(id, insert=(x,y), text_anchor='middle', alignment_baseline="middle", font_size=self.cell_size * 1.5, fill='black')
            dwg.add(text)        
        
        dwg.save()


    def draw_misc(self, dwg) -> None: 
        """Function draws entry points, exit points and staircase.""" 
        # ENTRY
        if self.entry is not None:
            if isinstance(self.entry, Rectangle):
                staircase_group = dwg.g()
                stripe_count = 8
                pattern_width = self.entry.width
                pattern_height = self.entry.height
                stripe_width = pattern_width / stripe_count
                
                y = self.entry.top
                for i in range(stripe_count):
                    x = self.entry.left + (i * stripe_width)
                   
                    stripe = dwg.rect(insert=(x, y), size=(stripe_width, pattern_height), fill='white', stroke='black')
                    staircase_group.add(stripe)

                if self.entry_direction == "top" or self.entry_direction == "bottom":
                    staircase_group.rotate(90, center=(self.entry.left + pattern_width / 2, self.entry.top + pattern_height / 2))

                dwg.add(dwg.rect((self.entry.left, self.entry.top), (self.entry.width, self.entry.height), fill="white", stroke="blue"))
                dwg.add(staircase_group)  
            else:
                entry_x, entry_y = self.entry
                if self.entry_direction == "left": 
                    dwg.add(dwg.rect((entry_x, entry_y), (self.cell_size, self.cell_size), fill="blue"))
                elif self.entry_direction == "right":
                    dwg.add(dwg.rect((entry_x - self.cell_size, entry_y), (self.cell_size, self.cell_size), fill="blue"))
                elif self.entry_direction == "top":
                    dwg.add(dwg.rect((entry_x, entry_y), (self.cell_size, self.cell_size), fill="blue"))
                else:
                    dwg.add(dwg.rect((entry_x, entry_y - self.cell_size), (self.cell_size, self.cell_size), fill="blue"))
        # EXIT
        if self.exit is not None:
            if isinstance(self.exit, Rectangle):
                staircase_group = dwg.g()
                stripe_count = 8
                pattern_width = self.exit.width
                pattern_height = self.exit.height
                stripe_width = pattern_width / stripe_count
                
                for i in range(stripe_count):
                    if self.exit_direction == "right":
                        x = self.exit.left + (i * stripe_width)
                        y = self.exit.top + i
                        width = stripe_width
                        height = pattern_height - i * 2
                    else:
                        x = self.exit.left + (i * stripe_width)
                        y = (self.exit.top + stripe_count) - i
                        width = stripe_width
                        height = (pattern_height - stripe_count * 2) + i * 2
                    
                    stripe = dwg.rect(insert=(x, y), size=(width, height), fill='white', stroke='black')
                    staircase_group.add(stripe)

                if self.exit_direction == "top":
                    staircase_group.rotate(90, center=(self.exit.left + pattern_width / 2, self.exit.top + pattern_height / 2))
                elif self.exit_direction == "bottom":
                    staircase_group.rotate(270, center=(self.exit.left + pattern_width / 2, self.exit.top + pattern_height / 2))
                dwg.add(dwg.rect((self.exit.left, self.exit.top), (self.exit.width, self.exit.height), fill="white", stroke="red"))
                dwg.add(staircase_group)
                
            else:
                exit_x, exit_y = self.exit
                if self.exit_direction == "left":   
                    dwg.add(dwg.rect((exit_x, exit_y), (self.cell_size, self.cell_size), fill="red"))
                elif self.exit_direction == "right":
                    dwg.add(dwg.rect((exit_x - self.cell_size, exit_y), (self.cell_size, self.cell_size), fill="red"))
                elif self.exit_direction == "top":
                    dwg.add(dwg.rect((exit_x, exit_y), (self.cell_size, self.cell_size), fill="red"))
                else:
                    dwg.add(dwg.rect((exit_x, exit_y - self.cell_size), (self.cell_size, self.cell_size), fill="red"))

class BSPNode:
    def __init__(self, bounds) -> None:
        self.left_child = None
        self.right_child = None
        self.bounds = bounds
        self.room = None
        self.corridors = []


    def partition(self, min_width: int, min_height: int, cell_size: int) -> None:
        """Create new nodes by dividing the node area along a horizontal or vertical line
          and repeat on new nodes until the node bounds are smaller or equal to minimum size.

        Args:
            min_width (int): Minimum width of partitioned subspace
            min_height (int): Minimum heigth of partitioned subspace
            cell_size (int): Size of the cells in map pattern
        """
        if self.bounds.width <= 2*min_width or self.bounds.height <= 2*min_height:
            return
        
        split_horizontal = random.choice([True, False])
        
        if split_horizontal:
            split_y = round(random.randint(self.bounds.top + min_height, self.bounds.bottom - min_height) / cell_size) * cell_size
            rect_1 = Rectangle(self.bounds.left, self.bounds.top, self.bounds.width, split_y - self.bounds.top)
            rect_2 = Rectangle(self.bounds.left, split_y, self.bounds.width, self.bounds.bottom - split_y)
            if DISCARD_BY_RATIO:
                if (rect_1.height / rect_1.width) < H_RATIO or (rect_2.height / rect_2.width) < H_RATIO:
                    self.partition(min_width, min_height, cell_size)
                    return
        else:
            split_x = round(random.randint(self.bounds.left + min_width, self.bounds.right - min_width) / cell_size) * cell_size
            rect_1 = Rectangle(self.bounds.left, self.bounds.top, split_x - self.bounds.left, self.bounds.height)
            rect_2 = Rectangle(split_x, self.bounds.top, self.bounds.right - split_x, self.bounds.height)
            if DISCARD_BY_RATIO:
                if (rect_1.width / rect_1.height) < W_RATIO or (rect_2.width / rect_2.height) < W_RATIO:
                    self.partition(min_width, min_height, cell_size)
                    return
        
        self.left_child = BSPNode(rect_1)
        self.right_child = BSPNode(rect_2)

        self.left_child.partition(min_width, min_height, cell_size)
        self.right_child.partition(min_width, min_height, cell_size)


    def create_room(self, min_width: int, min_height: int, cell_size: int) -> None:
        """Function places a room within nodes boundaries.

        Args:
            min_width (int): Minimum room width
            min_height (int): Minimum room height
            cell_size (int): Size of the cells in map pattern
        """
       
        room_width = random.randrange(min_width, self.bounds.width - cell_size * 2 + 1, cell_size) 
        room_height = random.randrange(min_height, self.bounds.height - cell_size * 2 + 1, cell_size)
        room_left = random.randrange((math.ceil(self.bounds.left / cell_size) * cell_size) + cell_size, self.bounds.right - room_width - cell_size + 1, cell_size)
        room_top = random.randrange((math.ceil(self.bounds.top / cell_size) * cell_size) + cell_size, self.bounds.bottom - room_height - cell_size + 1, cell_size)

        self.room = Rectangle(room_left, room_top, room_width, room_height)
     

    def get_room(self):
        """Return the closest room in the tree structure."""
        if self.left_child is None and self.right_child is None:
            return self.room
        if self.left_child is not None:
            return self.left_child.get_room()
        if self.right_child is not None:
            return self.right_child.get_room()


    def get_leaf_nodes(self) -> list:
        """Returns array of leaf nodes."""
        if self.left_child is None and self.right_child is None:
            return [self]
        else:
            return self.left_child.get_leaf_nodes() + self.right_child.get_leaf_nodes()


    def create_sibling_corridor(self, left_child, right_child, corridor_size: int) -> None:
        """Function creates corridor for two sibling nodes.

        Args:
            left_child (BSPNode): Left child of caller node
            right_child (BSPNode): Right child of caller node
            corridor_size (int): Corridor size
        """
        room_1 = left_child.get_room()
        room_2 = right_child.get_room()

        point_1 = room_1.center_rounded(corridor_size)
        point_2 = room_2.center_rounded(corridor_size)

        horizontal_dif = point_2[0] - point_1[0]
        vertical_dif = point_2[1] - point_1[1]

        horizontal_dif_rounded = round(abs(horizontal_dif) / corridor_size) * corridor_size
        vertical_dif_rounded  = round(abs(vertical_dif) / corridor_size) * corridor_size

        # room_1 is on the right of room_2
        if horizontal_dif < 0:
            if vertical_dif < 0: # room_2 is above room_1
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_2[0], point_1[1], abs(horizontal_dif_rounded), corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_2[1], corridor_size, abs(vertical_dif)))
                else:
                    self.corridors.append(Rectangle(point_2[0], point_2[1], abs(horizontal_dif_rounded) + corridor_size, corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_2[1], corridor_size, abs(vertical_dif_rounded)))
            elif vertical_dif > 0: # room_1 is above room_2
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_2[0], point_1[1], abs(horizontal_dif_rounded), corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_1[1], corridor_size, abs(vertical_dif_rounded)))
                else:
                    self.corridors.append(Rectangle(point_2[0], point_2[1], abs(horizontal_dif_rounded) + corridor_size, corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_1[1], corridor_size, abs(vertical_dif_rounded)))
            else: # same vertical
                self.corridors.append(Rectangle(point_2[0], point_2[1], abs(horizontal_dif_rounded), corridor_size))
        elif horizontal_dif > 0:   # room_2 is on the right of room_1
            if vertical_dif < 0:   # room_2 is above room_1
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_1[0], point_2[1], abs(horizontal_dif_rounded), corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_2[1], corridor_size, abs(vertical_dif_rounded)))
                else:
                    self.corridors.append(Rectangle(point_1[0], point_1[1], abs(horizontal_dif_rounded) + corridor_size, corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_2[1], corridor_size, abs(vertical_dif_rounded)))
            elif vertical_dif > 0:  # room_1 is above room_2
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_1[0], point_1[1], abs(horizontal_dif_rounded), corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_1[1], corridor_size, abs(vertical_dif_rounded)))
                else:
                    self.corridors.append(Rectangle(point_1[0], point_2[1], abs(horizontal_dif_rounded) + corridor_size, corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_1[1], corridor_size, abs(vertical_dif_rounded)))
            else:
                self.corridors.append(Rectangle(point_1[0], point_1[1], abs(horizontal_dif_rounded), corridor_size))
        else:   # same horizontal
            if vertical_dif < 0: 
                self.corridors.append(Rectangle(point_2[0], point_2[1], corridor_size, abs(vertical_dif_rounded)))
            elif vertical_dif > 0:
                self.corridors.append(Rectangle(point_1[0], point_1[1], corridor_size, abs(vertical_dif_rounded)))


    def draw_rooms(self, svg_document, cell_size: int) -> list:
        """Function draws rooms."""
        floor_index = 0
        room_numbers = []
        for node in self.get_leaf_nodes():
            floor_index = self.get_leaf_nodes().index(node)
            pattern = svg_document.defs.add(
                svg_document.pattern(size=(cell_size, cell_size), patternUnits="userSpaceOnUse"))
            pattern.add(svg_document.rect((0, 0), (cell_size, cell_size), fill="white", stroke="gray"))
            group = svg_document.add(svg_document.g())
            group.add(svg_document.rect((node.room.left, node.room.top), (node.room.width, node.room.height), fill=pattern.get_paint_server(), stroke="black",  stroke_width=1))
            room_numbers.append({"id": str(floor_index + 1), "insert_x": (node.room.left + node.room.right)/2, "insert_y": (node.room.bottom + node.room.top)/2})
        return room_numbers    

    def create_corridors(self, corridor_size: int) -> None:
        """Function iterates over the tree and creates corridors for sibling nodes."""
        if self.left_child is None and self.right_child is None:
            return

        self.left_child.create_corridors(corridor_size)
        self.right_child.create_corridors(corridor_size)

        self.create_sibling_corridor(self.left_child, self.right_child, corridor_size)


    def draw_corridors(self, svg_document, cell_size: int) -> None:
        """Function draws corridors"""
        if self.left_child is None and self.right_child is None:
            return
        pattern = svg_document.defs.add(
            svg_document.pattern(size=(cell_size, cell_size), patternUnits="userSpaceOnUse"))
        pattern.add(svg_document.rect((0, 0), (cell_size, cell_size), fill="white", stroke="gray"))
        if self.corridors:
            for corridor in self.corridors:
                group = svg_document.add(svg_document.g())
                map_corridor = group.add(svg_document.rect((corridor.left, corridor.top), (corridor.width, corridor.height), fill=pattern.get_paint_server()))   

        self.left_child.draw_corridors(svg_document, cell_size)
        self.right_child.draw_corridors(svg_document, cell_size)

    def get_corridors(self) -> list:
        """Return all corridors of the map."""
        corridors = []
        if self is None:
            return []

        if self.corridors:
            corridors.extend(self.corridors)

        if self.left_child is not None:
            corridors.extend(self.left_child.get_corridors())

        if self.right_child is not None:
            corridors.extend(self.right_child.get_corridors())
        
        return corridors
        

class Rectangle:
    def __init__(self, left, top, width, height) -> None:
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.right = left + width
        self.bottom = top + height

    def center(self) -> tuple:
        """Return the center of the rectangle"""
        center_x = (self.left + self.right)/2
        center_y = (self.top + self.bottom)/2
        return (center_x, center_y)


    def center_rounded(self, rounded_to_multiple) -> tuple:
        """Return a rounder center of the rectangle"""
        center_x = round(((self.left + self.right)/2) / rounded_to_multiple) * rounded_to_multiple
        center_y = round(((self.top + self.bottom)/2) / rounded_to_multiple) * rounded_to_multiple
        return (center_x, center_y)