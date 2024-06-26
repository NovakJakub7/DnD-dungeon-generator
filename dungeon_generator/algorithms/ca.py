import numpy as np
import svgwrite
import queue
import pathlib
import math
import copy
from scipy.spatial import KDTree
from numbers import Number
from svglib.svglib import svg2rlg
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from .desc_generator import DescriptionGenerator, calculate_party_level, level_description_to_text, ENCOUNTER_NUMBERS


FLOOR: int = 0
ROCK: int = 1
START: int = 2
EXIT: int = 3
RNG = np.random     
N: int = 4   # pocet iteraci CA
T: int = 5   # počet kamene kolem, aby byl prvek taky kamen
F: Number = .5 # pravděpodobnost že bude bunka v čase t=0 volná


class CADungeon:
    def __init__(self, save_path, cell_size: int, motif: str, average_player_level: int, number_of_players: int, total_treasure_value: int, db_conn = None, number_of_floors: int = 1) -> None:
        self.db_conn = db_conn
        self.average_player_level = average_player_level
        self.number_of_players = number_of_players
        self.total_treasure_value = total_treasure_value
        self.dungeon_motif = motif
        self.svg_cell_size = cell_size
        self.save_path = save_path
        self.number_of_floors = number_of_floors

    def generate_dungeon(self, rows: int, cols: int, seed: int, floor_probability: Number = F, number_of_iterations: int = N, rock_threshold: int = T) -> list:
        """Function uses Cellular Automata to generate one or more dungeons with descriptions and saves them as SVG images.

        Args:
            rows (int): Number of rows in map
            cols (int): Number of columns in map
            seed (int): Map seed
            floor_probability (Number, optional): Probability of cell being of type Floor when the map grid is initialized. Defaults to F.
            number_of_iterations (int, optional): Number of cellular automata iterations. Defaults to N.
            rock_threshold (int, optional): Number of rocks next to a cell to turn the cell into a rock. Defaults to T.

        Returns:
            list: Dungeon description
        """
        caves = []
        dungeon_description = []

        package_path = pathlib.Path.cwd()
        pdf_dir = package_path.joinpath("dungeon_generator", "static","images")

        for i in range(0, self.number_of_floors):
            file_name = f"map_ca_{i}.svg"
            pdf_file_name = f"map_ca_{i}.pdf"
            if i > 0:
                ca_cave = CACave(rows, cols, seed + i, floor_probability, number_of_iterations, rock_threshold, upper_cave=caves[i - 1])
            else:
                ca_cave = CACave(rows, cols, seed, floor_probability, number_of_iterations, rock_threshold)
            caves.append(ca_cave.generate_map())
            desc = ca_cave.place_monsters_items(self.db_conn, self.dungeon_motif, self.average_player_level, self.number_of_players, self.total_treasure_value)
            ca_cave.make_svg(self.svg_cell_size, save_path=self.save_path, file_name=file_name) 
            
            level_description = {'level_id': i, 'desc_list': desc, 'svg_file': file_name, 'pdf_file': pdf_file_name}
            dungeon_description.append(level_description)

            self.convert_svg_to_pdf(self.save_path.joinpath(file_name), pdf_dir.joinpath(pdf_file_name), (self.svg_cell_size * cols), (self.svg_cell_size * rows), level_description)   

        return dungeon_description


    def convert_svg_to_pdf(self, input_svg, output_pdf, width, height, level_desc) -> None:
        """Convert svg map and map description to pdf using reportlab library.

        Args:
            input_svg (Path): SVG file path
            output_pdf (Path): Output PDF path
            width (Int): SVG width
            height (Int): SVG height
            level_desc (list): Level description
        """
        # Create a new PDF canvas
        size = (width + 100, height + 100)
        c = canvas.Canvas(str(output_pdf), pagesize=landscape(size))

        # Load the SVG image using svglib
        drawing = svg2rlg(input_svg)

        # Set the position and scale of the SVG image on the canvas
        image_width = drawing.width
        image_height = drawing.height
        x = (size[0] - image_width) / 2
        y = size[1] - image_height - 50

        # Draw the SVG image on the canvas
        renderPDF.draw(drawing, c, x, y)

        # Make new page
        c.showPage()

        text = level_description_to_text(level_desc, "CA")
       
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

    

class CACave:
    def __init__(self, rows: int, cols: int, seed: int, floor_probability: Number = F, number_of_iterations: int = N, rock_threshold: int = T, upper_cave = None) -> None:
        self.rows = rows
        self.cols = cols
        self.map = []
        self.floor_probability = floor_probability
        self.number_of_iterations = number_of_iterations
        self.rock_threshold = rock_threshold
        self.caves = []
        self.upper_cave = upper_cave
        self.start_cell = ()
        self.exit_cell = ()
        self.svg_name = ""
        RNG.seed(seed)


    def generate_map(self):
        """Function generates grid map using Cellular Automata."""
        self.map = self.generate_grid()

        for _ in range(self.number_of_iterations):
            self.do_simulation_step()
        
        # ohranicim celou mapu kamenem
        self.map[0,:] = ROCK
        self.map[-1,:] = ROCK
        self.map[:,0] = ROCK
        self.map[:,-1] = ROCK

        self.process_map()
        
        return self


    def make_svg(self, cell_size, save_path, file_name) -> None:
        """ Makes svg image from map and saves it to path.
        """
        self.svg_name = file_name

        # Combine the path and filename to create the full file path
        file_path = save_path.joinpath(file_name)

        canvas_width = '{}px'.format(cell_size * self.cols)
        canvas_height = '{}px'.format(cell_size * self.rows)

        # Create a Drawing object and specify the file path
        dwg = svgwrite.Drawing(file_path, profile='full', size=(canvas_width, canvas_height))

        for x, row in enumerate(self.map):
            for y, cell in enumerate(row):
                if cell == FLOOR:
                    #group = dwg.add(dwg.g())
                    #group.add(dwg.rect((y*CELL_SIZE, x*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='white', stroke='grey', stroke_width=1))
                    dwg.add(dwg.rect((y*cell_size, x*cell_size), (cell_size, cell_size), fill='white', stroke='grey', stroke_width=1))
                elif cell == START:
                    dwg.add(dwg.rect((y*cell_size, x*cell_size), (cell_size, cell_size), fill='blue'))
                elif cell == EXIT:
                    dwg.add(dwg.rect((y*cell_size, x*cell_size), (cell_size, cell_size), fill='red'))
                else:
                    dwg.add(dwg.rect((y*cell_size, x*cell_size), (cell_size, cell_size), fill='black', stroke="black"))

        for cave in self.caves:
            x, y = cave.find_id_cell()

            group = dwg.add(dwg.g())
            group.add(dwg.rect((y*cell_size, x*cell_size), (cell_size, cell_size), fill='white', stroke='grey', stroke_width=1))

            cave_index = self.caves.index(cave)
            group.add(dwg.text(str(cave_index + 1), insert=(y * cell_size + cell_size / 2, x * cell_size + cell_size / 2), text_anchor='middle', alignment_baseline="middle", font_size=cell_size * 1.5, fill='black'))
    
        dwg.save()

    def generate_grid(self):
        """Returns two dimensional grid of FlOOR and ROCK cells.
        """
        grid = self.generate_row()

        for _ in range(self.rows - 1):
            grid = np.vstack((grid, self.generate_row()))

        return grid
    

    def generate_row(self):
        """Return an array of FLOOR and ROCK cells based on floor_probability.
        """

        row = RNG.choice([FLOOR, ROCK], self.cols, p=[self.floor_probability, 1 - self.floor_probability])
    
        return row
    

    def do_simulation_step(self) -> None:
        """Create new map grid based on the number of bordering rock cells for each map cell.
        """
        new_grid = np.zeros((self.rows, self.cols))

        for row_index in range(self.rows):
            for col_index in range(self.cols):
                rock_count = self.count_bordering_rocks(row_index, col_index)  
                if rock_count >= self.rock_threshold:
                    new_grid[row_index][col_index] = ROCK
                else:
                    new_grid[row_index][col_index] = FLOOR

        self.map = new_grid


    def count_bordering_rocks(self, x: int, y: int) -> int:
        """Return number of bordering rock cells of a cell on (x,y) coordinates.

        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        rock_count = 0
    
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                neighbour_x = x + dx
                neighbour_y = y + dy
                if not (neighbour_x == 0 and neighbour_y == 0): # nepocitam prvek (x,y)
                    if not self.is_in_map(neighbour_x, neighbour_y): # pokud je prvek mimo grid
                        rock_count += 1
                    elif self.map[neighbour_x][neighbour_y]: # pokud je prvek ROCK (1)
                        rock_count += 1
        
        return rock_count
    

    def is_in_map(self, x, y):
        """Return True if (x,y) cell is in map, otherwise return False.

        Args:
            x (int): X coordinate of the cell
            y (int): Y coordinate of the cell
        """
        return x >= 0 and y >= 0 and x < self.rows and y < self.cols
    

    def process_map(self, rock_threshold_size:int = 10, floor_threshold_size:int = 10) -> None:
        """Process the map by filling small unwanted regions and connecting remaining caves.

        Args:
            rock_threshold_size (int, optional): Size of a rock region to be filled. Defaults to 10.
            floor_threshold_size (int, optional): Size of a floor region to be filled. Defaults to 10.
        """
        rock_regions = self.get_regions(ROCK)

        for rock_region in rock_regions:
            if len(rock_region) < rock_threshold_size:
                for cell in rock_region:
                    cell_x, cell_y = cell
                    self.map[cell_x, cell_y] = FLOOR
        
        floor_regions = self.get_regions(FLOOR)

        for floor_region in floor_regions:
            if len(floor_region) < floor_threshold_size:
                for cell in floor_region:
                    cell_x, cell_y = cell
                    self.map[cell_x, cell_y] = ROCK
            else:
                self.caves.append(Cave(floor_region))      

        self.caves.sort(reverse=True, key=Cave.get_cave_size)
        
        if self.caves:
            self.caves[0].main_cave = True 
            self.caves[0].accessible_from_main_cave = True

            self.connect_close_caves()
            self.place_start_end()


    def get_regions(self, cell_type: int) -> list:
        """Return all regions of cells of cell_type

        Args:
            cell_type (int): Type of cell for which regions are searched.
        """
        regions = []
        map_flags = np.zeros((self.rows, self.cols))
        for x in range(self.rows):
            for y in range(self.cols):
                if map_flags[x, y] == 0 and self.map[x, y] == cell_type:
                    new_region = self.get_cells_region(x, y)
                    regions.append(new_region)

                    for cell in new_region:
                        cell_x, cell_y = cell
                        map_flags[cell_x, cell_y] = 1

        return regions
    

    def get_cells_region(self, start_x: int, start_y: int) -> list:
        """Return a list of cells of the same type next to each other called region. Starting at the (start_x, start_y) coordinates.

        Args:
            start_x (int): Starting X coordinate.
            start_y (int): Starting Y coordinate.
        """
        cells = []
        map_flags = np.zeros((self.rows, self.cols))
        cell_type = self.map[start_x, start_y]

        q = queue.Queue()
        q.put((start_x, start_y))

        while not q.empty():
            cell_x, cell_y = q.get()  
            if self.is_in_map(cell_x, cell_y):
                if map_flags[cell_x, cell_y] == 0 and self.map[cell_x, cell_y] == cell_type:
                    cells.append((cell_x, cell_y))
                    map_flags[cell_x, cell_y] = 1
                    q.put((cell_x+1, cell_y))
                    q.put((cell_x-1, cell_y))
                    q.put((cell_x, cell_y+1))
                    q.put((cell_x, cell_y-1))

        return cells
    

    def connect_close_caves(self, force_access_from_main: bool = False) -> None:
        """Connect the caves that are closest to each other.

        Args:
            force_access_from_main (bool, optional): Force accessability to all caves from main cave. Defaults to False.
        """
        accessible_caves_from_main = []
        not_accessible_caves_from_main = []
        
        if force_access_from_main:
            for cave in self.caves:
                if cave.accessible_from_main_cave:
                    accessible_caves_from_main.append(cave)
                else:
                    not_accessible_caves_from_main.append(cave)
        else:
            accessible_caves_from_main = self.caves
            not_accessible_caves_from_main = self.caves

        best_distance = 0
        possible_connection = False

        for cave in accessible_caves_from_main:
            if not force_access_from_main:
                possible_connection = False
                if len(cave.connected_caves) > 0:
                    continue

            for other_cave in not_accessible_caves_from_main:
                if cave == other_cave or cave.is_connected(other_cave):
                    continue

                closest_pair, min_distance = self.find_closest_pair(cave.cells, other_cave.cells)
                
                if min_distance < best_distance or not possible_connection:
                    best_distance = min_distance
                    coord_a, coord_b = closest_pair
                    possible_connection = True
                    best_cave = cave
                    best_other_cave = other_cave
                
            if possible_connection and not force_access_from_main:
                self.create_passage(best_cave, best_other_cave, coord_a, coord_b)

        if possible_connection and force_access_from_main:
            self.create_passage(best_cave, best_other_cave, coord_a, coord_b)
            self.connect_close_caves(True)

        if not force_access_from_main:
            self.connect_close_caves(True)        


    def find_closest_pair(self, region_a, region_b) -> tuple:
        """Find coordinates and distance of closest cells from two regions A and B using KDTree.

        Args:
            region_a (list): list of cells representing region A in cave
            region_b (list): list of cells representing region B in cave

        Returns:
            tuple: Coordinates and distance of closest cells
        """ 
       # Convert the cells in each region to points in the 2D space
        points_a = [(x, y) for x, y in region_a]
        points_b = [(x, y) for x, y in region_b]

        # Build a k-d tree for the points in region A
        tree = KDTree(points_a)

        # Initialize the closest pair of cells and the current minimum distance
        closest_pair = None
        min_distance = float('inf')

        # Search for the closest pair of cells
        for point in points_b:
            # Query the k-d tree to find the nearest neighbor(s) within the current distance threshold
            dist, idx = tree.query(point, k=2, distance_upper_bound=min_distance)
            
            # Check if the closest pair found so far is closer than the current pair
            if dist[0] < min_distance:
                closest_pair = (point, points_a[idx[0]])
                min_distance = dist[0]

            if dist[1] < min_distance:
                closest_pair = (point, points_a[idx[1]])
                min_distance = dist[1]

        return (closest_pair, min_distance)


    def create_passage(self, cave_a, cave_b, cell_a, cell_b) -> None:
        """Create passage using draw_circle between two caves A and B.

        Args:
            cave_a (_type_): instance of Cave
            cave_b (_type_): instance of Cave
            cell_a (tuple): coordinates of cell in cave_a
            cell_b (tuple): coordinates of cell in cave_b
        """
        cave_a.connect_caves(cave_b)
        line = self.get_line_coordinates(cell_a, cell_b)
        for cord in line:
            self.draw_circle(cord, 2)


    def draw_circle(self, cord, r) -> None:
        """Draw circle at specified coordinates with given radius.

        Args:
            cord (tuple): coordinates of circle
            r (number): circle radius
        """
        cx, cy = cord
        for x in range(-r, r):
            for y in range(-r, r):
                if x*x + y*y <= r*r:
                    draw_x = cx + x
                    draw_y = cy + y
                    if self.is_in_map(draw_x, draw_y):
                        self.map[draw_x, draw_y] = FLOOR


    def get_line_coordinates(self, start, end) -> list:
        """Function returns a list of tuples representing the coordinates of all the points on a line
        between start coordinates and end coordinates.

        Args:
            start (tuple): start coordinates
            end (tuple): end coordinates

        Returns:
            list: list of coordinates
        """
        x1, y1 = start
        x2, y2 = end

        coordinates = []
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        x_inc = dx / steps
        y_inc = dy / steps
        x = x1
        y = y1
        for _ in range(steps):
            coordinates.append((round(x), round(y)))
            x += x_inc
            y += y_inc
        coordinates.append((round(x2), round(y2)))
        return coordinates


    def place_start_end(self) -> None:
        """Function randomly places a start and an end inside the map. If there is more floors the end point will be the connection to next floor."""
        #ENTRY
        if self.upper_cave is None:
            # if no upper cave, choose random entry cell
            start_cave = RNG.choice(self.caves)
            start_cell_index = RNG.randint(0, start_cave.cave_size)
            start_x, start_y = start_cave.cells[start_cell_index]

            self.start_cell = (start_x, start_y)
            self.map[start_x][start_y] = START
        else:
            # if more caves, make random entry or entry same cell as the upper cave exit or the closest cell
            if RNG.random() < .5:
                # random entry cell
                start_cave = RNG.choice(self.caves)
                start_cell_index = RNG.randint(0, start_cave.cave_size)
                start_x, start_y = start_cave.cells[start_cell_index]

                self.start_cell = (start_x, start_y)
                self.map[start_x][start_y] = START
            else:
                # entry same as upper cave exit or closest
                # use flood-fill to find closest cell to upper cave exit
                upper_exit_x, upper_exit_y = self.upper_cave.exit_cell
                map_flags = np.zeros((self.rows, self.cols))

                q = queue.Queue()
                q.put((upper_exit_x, upper_exit_y))

                while not q.empty():
                    cell_x, cell_y = q.get()  
                    if self.is_in_map(cell_x, cell_y):
                        if map_flags[cell_x, cell_y] == 0 and self.map[cell_x, cell_y] == FLOOR:
                            start_x, start_y = cell_x, cell_y
                            break
                        else:
                            map_flags[cell_x, cell_y] = 1
                            q.put((cell_x+1, cell_y))
                            q.put((cell_x-1, cell_y))
                            q.put((cell_x, cell_y+1))
                            q.put((cell_x, cell_y-1))

                self.start_cell = self.upper_cave.exit_cell
                self.map[start_x][start_y] = START

        #EXIT
        # make random exit cell within specified range
        map_copy = copy.deepcopy(self.map)
        distance = float('inf')
        min_distance = (self.rows // 2 - 5) * (self.rows // 2 - 5) + (self.cols // 2 - 5) * (self.cols // 2 - 5)
        possible_exit = False
        
        while distance < min_distance or not possible_exit:
            exit_cave = RNG.choice(self.caves)
            exit_cell_index = RNG.randint(0, exit_cave.cave_size)
            exit_x, exit_y = exit_cave.cells[exit_cell_index]
            if FLOOR in map_copy:
                if map_copy[exit_x, exit_y] == FLOOR:
                    map_copy[exit_x, exit_y] = ROCK
                    distance = (exit_x - start_x) * (exit_x - start_x) + (exit_y - start_y) * (exit_y - start_y)
                    possible_exit = True
            else:
                distance = min_distance
                possible_exit = True
                exit_x, exit_y = (None, None)
        
        if exit_x is not None and exit_y is not None:
            self.exit_cell = (exit_x, exit_y)
            self.map[exit_x][exit_y] = EXIT
        

    def place_monsters_items(self, db_conn, motif: str, average_level: Number, number_of_players: Number, total_treasure_value: Number) -> list:
        """Function creates dictionary describing item and monster placement inside the dungeon.

        Args:
            db_conn (Connection): Database connection
            motif (String): Cave motif
            average_level (Number): Average player level
            number_of_players (Number): Number of players
            total_treasure_value (Number): Total treasure value

        Returns:
            list: Cave descriptions
        """
        encounter_level = calculate_party_level(average_level, number_of_players)
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
                motif = RNG.choice(available_motives)
                ratings = self.query_db(db_conn, 'select challenge_rating from monsters where motif = ?', [motif])
                rating_set = set([row["challenge_rating"] for row in ratings])
                encounter_set = set(ENCOUNTER_NUMBERS[encounter_level])
                if len(rating_set.intersection(encounter_set)) != 0:
                    motif_found = True
                else:
                    available_motives.pop(available_motives.index(motif))

        smaller_monsters_sizes = ["Fine", "Diminutive", "Tiny", "Small", "Medium"]
        larger_monsters_sizes = ["Medium", "Large", "Huge", "Gargantuan", "Colossal"]
        smaller_monsters = self.query_db(db_conn, "select * from monsters where size in ({}) and challenge_rating <= ? and motif = ?".format(','.join(['?'] * len(smaller_monsters_sizes))), smaller_monsters_sizes + [encounter_level, motif])
        larger_monsters = self.query_db(db_conn, "select * from monsters where size in ({}) and challenge_rating <= ? and motif = ?".format(','.join(['?'] * len(larger_monsters_sizes))), larger_monsters_sizes + [encounter_level, motif])
        items = self.query_db(db_conn, 'select * from items')
        dungeon_description = []
        
        number_of_caves = len(self.caves)
        if number_of_caves < 1:
            return []
        
        if number_of_caves < 5:
            large_caves_end_index = 1
        elif number_of_caves >= 5 and number_of_caves < 10:
            large_caves_end_index = math.floor(number_of_caves * 0.4)
        else:
            large_caves_end_index = math.floor(number_of_caves * 0.3)

        smallest_caves_start_index = number_of_caves - math.ceil(number_of_caves * 0.2)  
        
        # largest caves, large monsters and treasure
        for cave in self.caves[:large_caves_end_index]:
            if larger_monsters:
                monster_description = desc_generator.generate_monster_description(larger_monsters)
            else:
                monster_description = desc_generator.generate_monster_description(smaller_monsters)
            treasure_description = desc_generator.generate_treasure_description(items)
            dungeon_description.append({'cave_id': self.caves.index(cave), 'monster_desc': monster_description, 'treasure': treasure_description})    
        
        # smallest caves, treasure
        for cave in self.caves[smallest_caves_start_index:]:
            treasure_description = desc_generator.generate_treasure_description(items)
            dungeon_description.append({'cave_id': self.caves.index(cave), 'monster_desc': {}, 'treasure': treasure_description})
        
        # rest of the caves, smaller monsters or nothing
        for cave in self.caves[large_caves_end_index:smallest_caves_start_index]:
            monster_description = {}
            if RNG.random() < .4:
                if smaller_monsters:
                    monster_description = desc_generator.generate_monster_description(smaller_monsters)
            dungeon_description.append({'cave_id': self.caves.index(cave), 'monster_desc': monster_description, 'treasure': {}})

        dungeon_description = sorted(dungeon_description, key=lambda x: x['cave_id'])

        # add rest of the value to random cave
        if desc_generator.rest_of_value > 0:
            dungeon_description[len(dungeon_description) - 1]["treasure"]["gp"] += desc_generator.rest_of_value

        return dungeon_description


    def query_db(self, db_conn, query, args=(), one=False):
        """Query databse and return the result."""
        cur = db_conn.cursor().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv

class Cave:
    def __init__(self, cavecells: list) -> None:
        self.cells = cavecells
        self.cave_size = len(cavecells)
        self.connected_caves = []
        self.main_cave = False
        self.accessible_from_main_cave = False
        self.row_min = min(cavecells)[1]
        self.col_min = min(cavecells)[0]
        self.id_cell_x, self.id_cell_y = sorted(self.cells, key=lambda a: a[0])[self.cave_size // 2]


    def get_cave_size(self) -> int:
        """Return cave size"""
        return self.cave_size
    
    def make_accessible_from_main(self) -> None:
        """Mark this cave and all connected caves as accessible from main cave."""
        if not self.accessible_from_main_cave:
            self.accessible_from_main_cave = True
            for connected_cave in self.connected_caves:
                connected_cave.make_accessible_from_main()

    def connect_caves(self, other_cave) -> None:
        """Connects two caves.

        Args:
            other_cave (Cave): Cave to be connected
        """
        if self.accessible_from_main_cave:
            other_cave.make_accessible_from_main()
        elif other_cave.accessible_from_main_cave:
            self.make_accessible_from_main()

        self.connected_caves.append(other_cave)
        other_cave.connected_caves.append(self)

    def is_connected(self, other_cave) -> bool:
        """Checks if other cave is connected.

        Args:
            other_cave (Cave): Cave to check connection with

        Returns:
            bool: is cave connected to other_cave
        """

        return other_cave in self.connected_caves
    
    
    def find_id_cell(self):
        x = 0
        y = 0
        for cell in self.cells:
            x,y = cell
            is_suitable = True
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    neighbour_x = x + dx
                    neighbour_y = y + dy
                    if (neighbour_x, neighbour_y) not in self.cells:
                        is_suitable = False
                if not is_suitable:
                    break
            if is_suitable:
                break

        return (x, y)

if __name__ == "__main__":
   
    d = CADungeon(r"C:\Users\jakub\Documents\studium\DnD-dungeon-generator\dungeon_generator\static\svg", 10, None, 1)
    caves = d.generate_dungeon(55, 55, 9509, 0.3, 3, 5)
    