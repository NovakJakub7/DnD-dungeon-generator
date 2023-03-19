import numpy as np
import svgwrite
import queue

FLOOR = 0
ROCK = 1
WALL = 2
RNG = np.random     
N = 5   # pocet iteraci CA
T = 5   # počet kamene kolem, aby byl prvek taky kamen


def generate_map(rows, cols, floor_probability=0.45, number_of_iterations=N, rock_threshold=T):
    """Funkce vrací mapu podle CA algoritmu."""

    RNG.seed(123)
    # 123 pro 50x50


    map = generate_grid(rows, cols, floor_probability)

    for _ in range(number_of_iterations):
        map = do_simulation_step(map, rock_threshold)

    # ohranicim celou mapu kamenem
    map[0,:] = ROCK
    map[-1,:] = ROCK
    map[:,0] = ROCK
    map[:,-1] = ROCK
    
    return map


def process_map(map, rock_threshold_size=10, floor_threshold_size=10):
    """Z mapy odstraní samostatné regiony stěny/podlahy, podle určené meze."""

    rock_regions = get_regions(map, ROCK)
    remaining_rooms = []

    for rock_region in rock_regions:
        if len(rock_region) < rock_threshold_size:
            for cell in rock_region:
                cell_x, cell_y = cell
                map[cell_x, cell_y] = FLOOR
    
    floor_regions = get_regions(map, FLOOR)

    for floor_region in floor_regions:
        if len(floor_region) < floor_threshold_size:
            for cell in floor_region:
                cell_x, cell_y = cell
                map[cell_x, cell_y] = ROCK
        else:
            remaining_rooms.append(Room(floor_region, map))

    remaining_rooms.sort(reverse=True, key=Room.get_room_size)

    #for room in remaining_rooms:
    #    print(room.room_size)

    remaining_rooms[0].main_room = True
    remaining_rooms[0].accessible_from_main_room = True

    connect_close_rooms(remaining_rooms, map)        


def generate_grid(rows, cols, floor_probability):
    """Funkce vrací dvourozměrné pole s prvky FLOOR nebo ROCK podle zadané pravděpodobnosti výskytu."""

    grid = generate_row(cols, floor_probability)

    for _ in range(rows - 1):
        grid = np.vstack((grid, generate_row(cols, floor_probability)))

    return grid 


def generate_row(size, floor_probability):
    """Funkce vrací pole délky cols s prvky FLOOR nebo ROCK podle zadané pravděpodobnosti výskytu."""
    row = RNG.choice([FLOOR, ROCK], size, p=[floor_probability, 1 - floor_probability])
    
    return row


def do_simulation_step(grid, rock_threshold):
    """Funkce vrací nové dvourozměrné pole podle zadaného pole a použitých vývojových kroků."""

    # The single rule embedded in the cellular automata characterizes the cell as rock if the neighborhood value is greater
    # than or equal to T and as floor if otherwise; T equals 5 in this paper

    rows, cols = grid.shape
    new_grid = np.zeros((rows, cols))

    for row_index in range(rows):
        for col_index in range(cols):
            rock_count = count_bordering_rocks(grid, row_index, col_index)  
            if rock_count >= rock_threshold:
                new_grid[row_index][col_index] = ROCK
            else:
                new_grid[row_index][col_index] = FLOOR

    return new_grid


def count_bordering_rocks(grid, x, y):
    """Funkce vrací počet kamenu kolem prvku (x,y)."""
    rock_count = 0
    
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            neighbour_x = x + dx
            neighbour_y = y + dy
            if not (neighbour_x == 0 and neighbour_y == 0): # nepocitam prvek (x,y)
                if not is_in_map(neighbour_x, neighbour_y, grid): # pokud je prvek mimo grid
                    rock_count += 1
                elif grid[neighbour_x][neighbour_y]: # pokud je prvek ROCK (1)
                    rock_count += 1
    
    return rock_count


def is_in_map(x, y, map):
    """Vrací true pokud je prvek na souřadnicích (x, y) uvnitř mapy."""
    return x >= 0 and y >= 0 and x < len(map) and y < len(map[0])


def get_regions(map, cell_type):
    """Vrací pole regionů(pole souřadnic) v mapě, které mají daný typ."""
    rows = len(map)
    cols = len(map[0])

    regions = []
    map_flags = np.zeros((rows, cols))
    for x in range(rows):
        for y in range(cols):
            if map_flags[x, y] == 0 and map[x, y] == cell_type:
                new_region = get_cells_region(x, y, map)
                regions.append(new_region)

                for cell in new_region:
                    cell_x, cell_y = cell
                    map_flags[cell_x, cell_y] = 1

    return regions


def get_cells_region(start_x, start_y, map):
    """Vrací pole souřadnic prvků, které jsou stejného typu jako prvek (start_x, start_y)."""

    rows = len(map)
    cols = len(map[0])

    cells = []
    map_flags = np.zeros((rows, cols))
    cell_type = map[start_x, start_y]

    q = queue.Queue()
    q.put((start_x, start_y))

    while not q.empty():
        cell_x, cell_y = q.get()  
        if is_in_map(cell_x, cell_y, map):
            if map_flags[cell_x, cell_y] == 0 and map[cell_x, cell_y] == cell_type:
                cells.append((cell_x, cell_y))
                map_flags[cell_x, cell_y] = 1
                q.put((cell_x+1, cell_y))
                q.put((cell_x-1, cell_y))
                q.put((cell_x, cell_y+1))
                q.put((cell_x, cell_y-1))

    return cells
    #return map_flags
    

def make_svg_from_map(map):
    """Vytvoří a uloží z mapy svg soubor."""
    # Define the size of each cell in the map
    CELL_SIZE = 20

    filepath = './static/svg/map.svg'

    # Create a Drawing object and specify the file path
    dwg = svgwrite.Drawing(filepath)

    # Loop through the rows of the map
    for y, row in enumerate(map):
        # Loop through the columns of the map
        for x, cell in enumerate(row):
            # If the cell is non-zero, draw a rectangle
            if cell == FLOOR:
                dwg.add(dwg.rect((x*CELL_SIZE, y*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='white', stroke='black', stroke_width=1))
            else:
                dwg.add(dwg.rect((x*CELL_SIZE, y*CELL_SIZE), (CELL_SIZE, CELL_SIZE), fill='black'))

    # Save the SVG drawing to a file
    dwg.save()


def connect_close_rooms(all_rooms, map, force_access_from_main = False):

    accessible_rooms_from_main = []
    not_accessible_rooms_from_main = []

    if force_access_from_main:
        for room in all_rooms:
            if room.accessible_from_main_room:
                accessible_rooms_from_main.append(room)
            else:
                not_accessible_rooms_from_main.append(room)
    else:
        accessible_rooms_from_main = all_rooms
        not_accessible_rooms_from_main = all_rooms

    best_distance = 0
    possible_connection = False

    for room in accessible_rooms_from_main:
        if not force_access_from_main:
            possible_connection = False
            if len(room.connected_rooms) > 0:
                continue

        for other_room in not_accessible_rooms_from_main:
            if room == other_room or room.is_connected(other_room):
                continue

            for edge_cell in room.edge_cells:
                for other_edge_cell in other_room.edge_cells:
                    edge_cell_x, edge_cell_y = edge_cell
                    other_edge_cell_x, other_edge_cell_y = other_edge_cell
                    distance_between_rooms = pow(edge_cell_x - other_edge_cell_x, 2) + pow(edge_cell_y - other_edge_cell_y, 2)
                    
                    if distance_between_rooms < best_distance or not possible_connection:
                        best_distance = distance_between_rooms
                        possible_connection = True
                        best_cell = edge_cell
                        best_other_cell = other_edge_cell
                        best_room = room
                        best_other_room = other_room

        if possible_connection and not force_access_from_main:
            create_passage(best_room, best_other_room, best_cell, best_other_cell)
    
    if possible_connection and force_access_from_main:
        create_passage(best_room, best_other_room, best_cell, best_other_cell)
        connect_close_rooms(all_rooms, map, True)

    if not force_access_from_main:
        connect_close_rooms(all_rooms, map, True)


def create_passage(room, other_room, cell, other_cell):
    room.connect_rooms(other_room)
    print(cell, other_cell)
    line = get_line_coordinates(cell, other_cell)
    for cord in line:
        draw_circle(cord, 2, map)
        print(cord)
        

def draw_circle(cord, r, map):
    cx, cy = cord
    for x in range(-r, r):
        for y in range(-r, r):
            if x*x + y*y <= r*r:
                draw_x = cx + x
                draw_y = cy + y
                if is_in_map(draw_x, draw_y, map):
                    map[draw_x, draw_y] = FLOOR


def get_line_coordinates(start, end):
    """
    Function returns a list of tuples representing the coordinates of all the points on a line
    between start coordinates and end coordinates.
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


class Room:
    def __init__(self, roomcells, map) -> None:
        self.cells = roomcells
        self.room_size = len(roomcells)
        self.connected_rooms = []
        self.edge_cells = []
        self.main_room = False
        self.accessible_from_main_room = False

        for cell in self.cells:
            cell_x, cell_y = cell
            for row in range(-1, 2):
                for col in range(-1, 2):
                    neighbour_x = cell_x + row
                    neighbour_y = cell_y + col
                    if neighbour_x == cell_x or neighbour_y == cell_y:
                        if map[neighbour_x, neighbour_y] == ROCK:
                            self.edge_cells.append(cell)

    def get_room_size(self):
        return self.room_size
    
    def make_accessible_from_main(self):
        if not self.accessible_from_main_room:
            self.accessible_from_main_room = True
            for connected_room in self.connected_rooms:
                connected_room.make_accessible_from_main()

    def connect_rooms(self, other_room):
        """Connects two rooms."""

        if self.accessible_from_main_room:
            other_room.make_accessible_from_main()
        elif other_room.accessible_from_main_room:
            self.make_accessible_from_main()

        self.connected_rooms.append(other_room)
        other_room.connected_rooms.append(self)

    def is_connected(self, other_room):
        """Checks if other room is connected."""

        return other_room in self.connected_rooms
    
    

    

map = generate_map(50, 50, floor_probability=.5, number_of_iterations=4, rock_threshold=5)
process_map(map)
make_svg_from_map(map)
