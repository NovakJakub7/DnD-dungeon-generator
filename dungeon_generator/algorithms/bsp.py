import random
import svgwrite
import os
from svgwrite import pattern

DISCARD_BY_RATIO = True
H_RATIO = 0.45
W_RATIO = 0.45

# TODO:
#   start, exit, patra
#   vkládání nepřátel, kořisti

class BSPDungeon:
    def __init__(self, bounds, seed, save_path: str, db_conn = None, number_of_floors: int = 1) -> None:
        self.bounds = bounds
        self.seed = seed
        self.db_conn = db_conn
        self.save_path = save_path
        self.number_of_floors = number_of_floors

    def generate_dungeon(self, min_partition_width, min_partition_height):
        floors = []
        dungeon_description = []

        for i in range(0, self.number_of_floors):
            file_name = f"map_bsp_{i}.svg"
            if i > 0:
                pass
            else:
                bsp_tree = BSPTree(self.bounds, self.seed)
            floors.append(bsp_tree.create_map(min_partition_width, min_partition_height))
            #place monsters TO DO
            desc = bsp_tree.place_monsters_items(self.db_conn)
            bsp_tree.make_svg(self.save_path, file_name)

            level_description = {'level_id': i, 'desc_list': desc, 'svg_name': bsp_tree.svg_name}
            dungeon_description.append(level_description)


        return  dungeon_description


class BSPTree:
    def __init__(self, bounds, seed, upper_floor = None, floor_depth = 0, number_of_floors = 0) -> None:
        self.root = BSPNode(bounds)
        self.min_partition_width = 0
        self.min_partition_height = 0
        self.upper_floor = upper_floor #instance BSPTree reprezentujici vrchnejsi level, None kdyz není
        self.entry = ()
        self.exit = ()
        self.entry_direction = ""
        self.entry_size = 0
        self.floor_depth = floor_depth
        self.number_of_floors = number_of_floors
        self.svg_name = ""
        self.seed = seed
        random.seed(seed)
        

    def create_map(self, min_partition_width, min_partition_height) -> None:

        self.min_partition_width = min_partition_width
        self.min_partition_height = min_partition_height

        min_room_width = min_partition_width / 100 * 80
        min_room_height = min_partition_height / 100 * 80

        corridor_size = (min_partition_width + min_partition_height) / 20

        self.partition(min_partition_width, min_partition_height)
        self.create_rooms(min_room_width, min_room_height)
        self.create_corridors(corridor_size)
        self.place_entry_exit()

        return self


    def partition(self, min_width, min_height) -> None:
        """Apply space partitioning on root node."""
        self.root.partition(min_width, min_height)
        

    def get_leaf_nodes(self) -> list:
        """Returns list of leaf nodes."""
        return self.root.get_leaf_nodes()


    def create_rooms(self, min_width, min_height) -> None:
        """Creates a room for every leaf node in tree."""
        for node in self.get_leaf_nodes():
            node.create_room(min_width, min_height)


    def create_corridors(self, corridor_size) -> None:
        """Creates corridors between rooms of sibling nodes."""
        self.root.create_corridors(corridor_size)


    def get_rooms(self) -> list:
        """Returns a list of all Rooms"""
        nodes = self.get_leaf_nodes()
        rooms = []

        for node in nodes:
            rooms.append(node.room)

        return rooms

    def place_entry_exit(self) -> None:
        # POKRAČUJEME ZDE
        # mám souřadnice vstupu podle strany
        # dodelat: exit, vykreslovani spravne
        rooms = self.get_rooms()   
        
        # nemam vrchní patro, udelam random vstup na nejaké straně
        if self.upper_floor is None:
            # START
            self.entry_size = self.min_partition_width / 100 * 20
            entry_direction = random.choice(["left", "right", "top", "bottom"])
            #entry_direction = "left"

            if entry_direction == "left":
                entry_room = min(rooms, key=lambda x: x.left)
                entry_point = (entry_room.left, random.randint(entry_room.top + self.entry_size, entry_room.bottom - self.entry_size))
            elif entry_direction == "right":
                entry_room = max(rooms, key=lambda x: x.right)
                entry_point = (entry_room.right, random.randint(entry_room.top + self.entry_size, entry_room.bottom - self.entry_size))
            elif entry_direction == "top":
                entry_room = min(rooms, key=lambda x: x.top)
                entry_point = (random.randint(entry_room.left + self.entry_size, entry_room.right - self.entry_size), entry_room.top)
            else: # bottom
                entry_room = max(rooms, key=lambda x: x.bottom)
                entry_point = (random.randint(entry_room.left + self.entry_size, entry_room.right - self.entry_size), entry_room.bottom)

            print(entry_direction, entry_point)
            self.entry_direction = entry_direction
            self.entry = entry_point

            #EXIT
            # pokud je jen jedno patro nebo jsem poslední patro tak exit v random roomce
            if self.number_of_floors == 0 or self.floor_depth == self.number_of_floors:
                exit_direction = random.choice(["left", "right", "top", "bottom"])
                # nechceme stejny exit smer
                while exit_direction == entry_direction:
                    exit_direction = random.choice(["left", "right", "top", "bottom"])
                
        else: # mam vrchní patro, udělam vstup (schodiste) z exitu predchoziho patra (patro nahore nebo dole?)
            # exit bud v prvnim patre jako vstup nebo kdyz jdeme dolu tak exit jinam?
            pass           


    def place_monsters_items(self, db_conn):
        """Function creates dictionary describing item and monster placement inside the dungeon."""
        rooms = self.get_rooms()
        room_sizes = []
        number_of_rooms = len(rooms)
        for room in rooms:
            room_sizes.append(room.width * room.height)
        room_sizes.sort(reverse=True)
        #print(room_sizes)
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

        large_monsters = self.query_db(db_conn, 'select * from monsters where size = ?', ['Large'])
        medium_monsters = self.query_db(db_conn, 'select * from monsters where size = ?', ['Medium'])
        small_monsters = self.query_db(db_conn, 'select * from monsters where size = ?', ['Small'])
        items = self.query_db(db_conn, 'select * from items')
        dungeon_description = []
        
        for room in rooms:
            room_size = room.width * room.height
            if room_size >= large_size: # velke
                chosen_monsters = []
                chosen_monsters.append(large_monsters[random.randint(0, len(large_monsters) - 1)])
                chosen_monsters.append(medium_monsters[random.randint(0, len(medium_monsters) - 1)])

                chosen_item = items[random.randint(0, len(items) - 1)]

                dungeon_description.append({'cave_id': rooms.index(room), 'monsters': chosen_monsters, 'item': chosen_item}) 
            elif room_size < large_size and room_size > small_size: # medium
                chosen_monsters = []
                if random.random() < .5:
                    if random.random() < .5:
                        chosen_monsters.append(small_monsters[random.randint(0, len(small_monsters) - 1)])
                        chosen_monsters.append(medium_monsters[random.randint(0, len(medium_monsters) - 1)])
                    else:
                        chosen_monsters.append(small_monsters[random.randint(0, len(small_monsters) - 1)])
                        chosen_monsters.append(small_monsters[random.randint(0, len(small_monsters) - 1)])

                dungeon_description.append({'cave_id': rooms.index(room), 'monsters': chosen_monsters, 'item': None})

            else: # male
                chosen_item = items[random.randint(0, len(items) - 1)]
                dungeon_description.append({'cave_id': rooms.index(room), 'monsters': [], 'item': chosen_item})

        return sorted(dungeon_description, key=lambda x: x['cave_id'])


    def query_db(self, db_conn, query, args=(), one=False):
        cur = db_conn.cursor().execute(query, args)
        rv = cur.fetchall()
        cur.close()
        return (rv[0] if rv else None) if one else rv
    

    def make_svg(self, save_path, file_name):
        """Generate svg image from BSPTree and save it to path under the file name."""
        file_path = os.path.join(save_path, file_name)

        self.svg_name = file_name

        canvas_width = '{}px'.format(self.root.bounds.width)
        canvas_height = '{}px'.format(self.root.bounds.height)

        # Create a Drawing object and specify the file path
        dwg = svgwrite.Drawing(file_path, profile='full', size=(canvas_width, canvas_height))

        # black map background
        map = dwg.add(dwg.rect((self.root.bounds.left, self.root.bounds.top), (self.root.bounds.width, self.root.bounds.height)))
        map.fill('black')
        map.stroke('black', width=2)

        self.root.draw_corridors(dwg)
        self.root.draw_rooms(dwg)

        entry_x, entry_y = self.entry
        if self.entry_direction == "left" or self.entry_direction == "right":   
            dwg.add(dwg.rect((entry_x, entry_y), (10, self.entry_size), fill="blue"))
        else:
            dwg.add(dwg.rect((entry_x, entry_y), (self.entry_size, 10), fill="blue"))
        
        dwg.save()


class BSPNode:
    def __init__(self, bounds) -> None:
        #self.parent = BSPNode()
        self.left_child = None
        self.right_child = None
        self.bounds = bounds
        self.room = None
        self.corridors = []


    def partition(self, min_width, min_height):
        """Create new nodes by dividing the node area along a horizontal or vertical line
          and repeat on new nodes until the node bounds are smaller or equal to minimum size."""
        if self.bounds.width <= 2*min_width or self.bounds.height <= 2*min_height:
            return
        
        split_horizontal = random.choice([True, False])
        
        if split_horizontal:
            split_y = random.randint(self.bounds.top + min_height, self.bounds.bottom - min_height)
            rect_1 = Rectangle(self.bounds.left, self.bounds.top, self.bounds.width, split_y - self.bounds.top)
            rect_2 = Rectangle(self.bounds.left, split_y, self.bounds.width, self.bounds.bottom - split_y)
            if DISCARD_BY_RATIO:
                if (rect_1.height / rect_1.width) < H_RATIO or (rect_2.height / rect_2.width) < H_RATIO:
                    self.partition(min_width, min_height)
                    return
        else:
            split_x = random.randint(self.bounds.left + min_width, self.bounds.right - min_width)
            rect_1 = Rectangle(self.bounds.left, self.bounds.top, split_x - self.bounds.left, self.bounds.height)
            rect_2 = Rectangle(split_x, self.bounds.top, self.bounds.right - split_x, self.bounds.height)
            if DISCARD_BY_RATIO:
                if (rect_1.width / rect_1.height) < W_RATIO or (rect_2.width / rect_2.height) < W_RATIO:
                    self.partition(min_width, min_height)
                    return
        
        self.left_child = BSPNode(rect_1)
        self.right_child = BSPNode(rect_2)

        self.left_child.partition(min_width, min_height)
        self.right_child.partition(min_width, min_height)


    def create_room(self, min_width, min_height):
        """Places a room within nodes boundaries."""
        room_width = random.randint(min_width, self.bounds.width - 2)
        room_height = random.randint(min_height, self.bounds.height - 2)
        room_left = random.randint(self.bounds.left + 1, self.bounds.right - room_width - 1)
        room_top = random.randint(self.bounds.top + 1, self.bounds.bottom - room_height - 1)
        self.room = Rectangle(room_left, room_top, room_width, room_height)
     

    def get_room(self):
        if self.left_child is None and self.right_child is None:
            return self.room
        if self.left_child is not None:
            return self.left_child.get_room()
        if self.right_child is not None:
            return self.right_child.get_room()


    def get_leaf_nodes(self):
        """Returns array of leaf nodes."""
        if self.left_child is None and self.right_child is None:
            return [self]
        else:
            return self.left_child.get_leaf_nodes() + self.right_child.get_leaf_nodes()


    def create_sibling_corridor(self, left_child, right_child, corridor_size):
        room_1 = left_child.get_room()
        room_2 = right_child.get_room()

        #point_1 = (random.randint(room_1.left + corridor_size, room_1.right - corridor_size), random.randint(room_1.top + corridor_size, room_1.bottom - corridor_size))
        #point_2 = (random.randint(room_2.left + corridor_size, room_2.right - corridor_size), random.randint(room_2.top + corridor_size, room_2.bottom - corridor_size))

        point_1 = room_1.center()
        point_2 = room_2.center()

        horizontal_dif = point_2[0] - point_1[0]
        vertical_dif = point_2[1] - point_1[1]

        # room_1 is on the right of room_2
        if horizontal_dif < 0:
            if vertical_dif < 0: # room_2 is above room_1
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_2[0], point_1[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_2[1], corridor_size, abs(vertical_dif)))
                else:
                    self.corridors.append(Rectangle(point_2[0], point_2[1], abs(horizontal_dif) + corridor_size, corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_2[1], corridor_size, abs(vertical_dif)))
            elif vertical_dif > 0: # room_1 is above room_2
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_2[0], point_1[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_1[1], corridor_size, abs(vertical_dif)))
                else:
                    self.corridors.append(Rectangle(point_2[0], point_2[1], abs(horizontal_dif) + corridor_size, corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_1[1], corridor_size, abs(vertical_dif)))
            else: # same vertical
                self.corridors.append(Rectangle(point_2[0], point_2[1], abs(horizontal_dif), corridor_size))
        elif horizontal_dif > 0:   # room_2 is on the right of room_1
            if vertical_dif < 0:   # room_2 is above room_1
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_1[0], point_2[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_2[1], corridor_size, abs(vertical_dif)))
                else:
                    self.corridors.append(Rectangle(point_1[0], point_1[1], abs(horizontal_dif) + corridor_size, corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_2[1], corridor_size, abs(vertical_dif)))
            elif vertical_dif > 0:  # room_1 is above room_2
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_1[0], point_1[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_1[1], corridor_size, abs(vertical_dif)))
                else:
                    self.corridors.append(Rectangle(point_1[0], point_2[1], abs(horizontal_dif) + corridor_size, corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_1[1], corridor_size, abs(vertical_dif)))
            else:
                self.corridors.append(Rectangle(point_1[0], point_1[1], abs(horizontal_dif), corridor_size))
        else:   # same horizontal
            if vertical_dif < 0: 
                self.corridors.append(Rectangle(point_2[0], point_2[1], corridor_size, abs(vertical_dif)))
            elif vertical_dif > 0:
                self.corridors.append(Rectangle(point_1[0], point_1[1], corridor_size, abs(vertical_dif)))


    def draw_rooms(self, svg_document):
        floor_index = 0
        for node in self.get_leaf_nodes():
            floor_index = self.get_leaf_nodes().index(node)
            pattern = svg_document.defs.add(
                svg_document.pattern(size=(20, 20), patternUnits="userSpaceOnUse"))
            pattern.add(svg_document.rect((0, 0), (20, 20), fill="white", stroke="black"))

            group = svg_document.add(svg_document.g())
            group.add(svg_document.rect((node.room.left, node.room.top), (node.room.width, node.room.height), fill=pattern.get_paint_server()))
            group.add(svg_document.text(str(floor_index + 1), insert=((node.room.left + node.room.right)/2,(node.room.bottom + node.room.top)/ 2), text_anchor='middle', alignment_baseline="middle", font_size=20, fill='black'))

        

    def create_corridors(self, corridor_size):
        if self.left_child is None and self.right_child is None:
            return

        self.left_child.create_corridors(corridor_size)
        self.right_child.create_corridors(corridor_size)

        self.create_sibling_corridor(self.left_child, self.right_child, corridor_size)


    def draw_corridors(self, svg_document):
        if self.left_child is None and self.right_child is None:
            return
        
        if self.corridors:
            for corridor in self.corridors:
                group = svg_document.add(svg_document.g())
                map_corridor = group.add(svg_document.rect((corridor.left, corridor.top), (corridor.width, corridor.height), fill='white'))   
                #corridor_id = group.add(svg_document.text(id(self), insert=(corridor.left + 2, corridor.top - 2)))
                #corridor_id.fill('white')

        self.left_child.draw_corridors(svg_document)
        self.right_child.draw_corridors(svg_document)
        

class Rectangle:
    def __init__(self, left, top, width, height) -> None:
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.right = left + width
        self.bottom = top + height

    def center(self) -> tuple:
        center_x = (self.left + self.right)/2
        center_y = (self.top + self.bottom)/2
        return (center_x, center_y)


if __name__ == "__main__":
    bsp = BSPTree(Rectangle(0, 0, 800, 800), 1235)
    bsp.create_map(150, 150)
    bsp.make_svg(save_path=r"C:\Users\jakub\Documents\studium\DnD-dungeon-generator\dungeon_generator\static\svg", file_name=r"map_bsp.svg")
    
    

