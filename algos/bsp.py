import random
import svgwrite
import os

DISCARD_BY_RATIO = True
H_RATIO = 0.45
W_RATIO = 0.45

# TODO:
#   vytvoření chodeb mezi mistnostmi
#   začátek/vstup do dungeonu, další podlaží?
#   vkládání nepřátel, kořisti

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

        point_1 = (random.randint(room_1.left + corridor_size, room_1.right - corridor_size), random.randint(room_1.top + corridor_size, room_1.bottom - corridor_size))
        point_2 = (random.randint(room_2.left + corridor_size, room_2.right - corridor_size), random.randint(room_2.top + corridor_size, room_2.bottom - corridor_size))

        horizontal_dif = point_2[0] - point_1[0]
        vertical_dif = point_2[1] - point_1[1]

        # room_1 is on the right of room_2
        if horizontal_dif < 0:
            if vertical_dif < 0: # room_2 is above room_1
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_2[0], point_1[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_2[1], corridor_size, abs(vertical_dif)))
                else:
                    self.corridors.append(Rectangle(point_2[0], point_2[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_2[1], corridor_size, abs(vertical_dif)))
            elif vertical_dif > 0: # room_1 is above room_2
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_2[0], point_1[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_1[1], corridor_size, abs(vertical_dif)))
                else:
                    self.corridors.append(Rectangle(point_2[0], point_2[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_1[1], corridor_size, abs(vertical_dif)))
            else: # same vertical
                self.corridors.append(Rectangle(point_2[0], point_2[1], abs(horizontal_dif), corridor_size))
        elif horizontal_dif > 0:   # room_2 is on the right of room_1
            if vertical_dif < 0: 
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_1[0], point_2[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_2[1], corridor_size, abs(vertical_dif)))
                else:
                    self.corridors.append(Rectangle(point_1[0], point_1[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_2[1], corridor_size, abs(vertical_dif)))
            elif vertical_dif > 0:
                if random.choice([True, False]):
                    self.corridors.append(Rectangle(point_1[0], point_1[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_2[0], point_1[1], corridor_size, abs(vertical_dif)))
                else:
                    self.corridors.append(Rectangle(point_1[0], point_2[1], abs(horizontal_dif), corridor_size))
                    self.corridors.append(Rectangle(point_1[0], point_1[1], corridor_size, abs(vertical_dif)))
            else:
                self.corridors.append(Rectangle(point_1[0], point_1[1], abs(horizontal_dif), corridor_size))
        else:   # same horizontal
            if vertical_dif < 0: 
                self.corridors.append(Rectangle(point_2[0], point_2[1], corridor_size, abs(vertical_dif)))
            elif vertical_dif > 0:
                self.corridors.append(Rectangle(point_1[0], point_1[1], corridor_size, abs(vertical_dif)))


    def draw_rooms(self, svg_document):
        for node in self.get_leaf_nodes():
            room = svg_document.add(svg_document.rect((node.room.left, node.room.top), (node.room.width, node.room.height)))
            room.fill('white')


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
                print(corridor)
                map_corridor = svg_document.add(svg_document.rect((corridor.left, corridor.top), (corridor.width, corridor.height)))   
                map_corridor.fill('white')

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


class BSPTree:
    def __init__(self, bounds) -> None:
        self.root = BSPNode(bounds)
        

    def create_map(self, min_partition_width, min_partition_height):

        min_room_width = min_partition_width / 100 * 80
        min_room_height = min_partition_height / 100 * 80

        corridor_size = (min_partition_width + min_partition_height) / 20

        self.partition(min_partition_width, min_partition_height)
        self.create_rooms(min_room_width, min_room_height)
        self.create_corridors(corridor_size)


    def partition(self, min_width, min_height):
        """Apply space partitioning on root node."""
        self.root.partition(min_width, min_height)
        

    def get_leaf_nodes(self):
        """Returns array of leaf nodes."""
        return self.root.get_leaf_nodes()


    def create_rooms(self, min_width, min_height):
        """Creates a room for every leaf node in tree."""
        for node in self.get_leaf_nodes():
            node.create_room(min_width, min_height)


    def create_corridors(self, corridor_size):
        """Creates corridors between rooms of sibling nodes."""
        self.root.create_corridors(corridor_size)


    def bfs(self):
        queue = [self.root]
        nodes = []

        while len(queue) != 0:
            current_node = queue.pop(0)
            nodes.append(current_node)

            if current_node.left_child is not None:
                queue.append(current_node.left_child)
            if current_node.right_child is not None:
                queue.append(current_node.right_child)

        return nodes
        

    def make_svg(self):
        save_path = './static/svg/'

        file_name = "bsp_map.svg"

        # Combine the path and filename to create the full file path
        file_path = os.path.join(save_path, file_name)

        # Create a Drawing object and specify the file path
        dwg = svgwrite.Drawing(file_path)

        map = dwg.add(dwg.rect((self.root.bounds.left, self.root.bounds.top), (self.root.bounds.width, self.root.bounds.height)))
        map.fill('black')
        map.stroke('black', width=2)

        self.root.draw_rooms(dwg)
        self.root.draw_corridors(dwg)
        dwg.save()

bsp = BSPTree(Rectangle(0, 0, 800, 800))
bsp.create_map(200, 200)
bsp.make_svg()

#for node in bsp.get_leaf_nodes():
#    print(node.room)

