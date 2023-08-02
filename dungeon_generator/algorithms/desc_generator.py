import math
import random

ENCOUNTER_NUMBERS: list = [[0, 1, 2, 3, 4, 5, 8, 11],
                        [1, 0.5, 0.3, 0.25, 0.16, 0.125, 0.125],
                        [2, 1, 0.5, 0.5, 0.3, 0.25, 0.16],
                        [3, 2, 1, 0.5, 0.5, 0.3, 0.3],
                        [4, 2, 1, 1, 0.5, 0.5, 0.3],
                        [5, 3, 2, 1, 1, 0.5, 0.5],
                        [6, 4, 3, 2, 1, 1, 0.5],
                        [7, 5, 4, 3, 2, 1, 0.5], 
                        [8, 6, 5, 4, 3, 2, 1],
                        [9, 7, 6, 5, 4, 3, 2],
                        [10, 8, 7, 6, 5, 4, 3],
                        [11, 9, 8, 7, 6, 5, 4],
                        [12, 10, 9, 8, 7, 6, 5],
                        [13, 11, 10, 9, 8, 7, 6],
                        [14, 12, 11, 10, 9, 8, 7],
                        [15, 13, 12, 11, 10, 9, 8],
                        [16, 14, 13, 12, 11, 10, 9],
                        [17, 15, 14, 13, 12, 11, 10],
                        [18, 16, 15, 14, 13, 12, 11],
                        [19, 17, 16, 15, 14, 13, 12],
                        [19, 18, 17, 16, 15, 14, 13]]

TREASURE: list = [{"number_of_dice": 2, "dice_size": 8, "treasure_base": 10},
                  {"number_of_dice": 4, "dice_size": 10, "treasure_base": 10},
                  {"number_of_dice": 1, "dice_size": 4, "treasure_base": 100},
                  {"number_of_dice": 1, "dice_size": 6, "treasure_base": 100},
                  {"number_of_dice": 1, "dice_size": 8, "treasure_base": 100},
                  {"number_of_dice": 1, "dice_size": 10, "treasure_base": 100},
                  {"number_of_dice": 2, "dice_size": 6, "treasure_base": 100},
                  {"number_of_dice": 2, "dice_size": 8, "treasure_base": 100},
                  {"number_of_dice": 5, "dice_size": 4, "treasure_base": 100},
                  {"number_of_dice": 6, "dice_size": 4, "treasure_base": 100},
                  {"number_of_dice": 4, "dice_size": 8, "treasure_base": 100},
                  {"number_of_dice": 1, "dice_size": 4, "treasure_base": 1000},
                  {"number_of_dice": 1, "dice_size": 4, "treasure_base": 1000},
                  {"number_of_dice": 1, "dice_size": 6, "treasure_base": 1000},
                  {"number_of_dice": 1, "dice_size": 8, "treasure_base": 1000},
                  {"number_of_dice": 1, "dice_size": 12, "treasure_base": 1000},
                  {"number_of_dice": 3, "dice_size": 4, "treasure_base": 1000},
                  {"number_of_dice": 3, "dice_size": 6, "treasure_base": 1000},
                  {"number_of_dice": 3, "dice_size": 8, "treasure_base": 1000},
                  {"number_of_dice": 4, "dice_size": 8, "treasure_base": 1000}]


class DescriptionGenerator:
    def __init__(self, encounter_level: int, total_treasure_value: int) -> None: 
        self.encounter_level = encounter_level
        self.total_treasure_value = total_treasure_value
        self.rest_of_value = total_treasure_value

    def generate_monster_description(self, monsters: list) -> dict:
        """Function generates monsters and their number of occurences for a room.

        Args:
            monsters (list): list available monsters

        Returns:
            dict: Monster and number of occurrences
        """
        monster = random.choice(monsters)
        cr = monster['challenge_rating']

        while cr not in ENCOUNTER_NUMBERS[self.encounter_level]:
            monster = random.choice(monsters)
            cr = monster['challenge_rating']

        ecl_row = ENCOUNTER_NUMBERS[self.encounter_level]
        # find challenge rating base on ENCOUNTER_NUMBERS table
        if cr not in ecl_row:
            cr = self.encounter_level
        # find index
        row_index = ecl_row.index(cr) + 1
        # values in row at index 0 are the number of monsters
        number_of_monsters = ENCOUNTER_NUMBERS[0][row_index]
        # if more than 5 monsters, add or substract one monster
        if number_of_monsters > 5:
            number_of_monsters = random.randint(number_of_monsters - 1, number_of_monsters + 1)
        
        return {'monster': monster, 'number_of_monsters': number_of_monsters}


    def generate_treasure_description(self, items: list) -> dict:
        """Function generates treasure description for a room.

        Args:
            items (list): Available items

        Returns:
            dict: Treasure description containing item and/or gp
        """
        item = None
        gp = 0
        both = random.choice([False, True])
        only_item = random.choice([False, True])
        lowest_price = sorted(items, key=lambda x: x["price"])[0]["price"]

        # random items / gp based on player level
        if self.total_treasure_value < 0:
            treasure_row = TREASURE[self.encounter_level - 1]
            max_gp = self.roll_dice(treasure_row["number_of_dice"], treasure_row["dice_size"]) * treasure_row["treasure_base"]
            min_gp = max_gp - treasure_row["treasure_base"]
            gp = random.randint(min_gp, max_gp)
            item = random.choice(items)
        elif self.rest_of_value > 0:
            # pick items and gp based on total treasure value
            if self.rest_of_value > lowest_price and both:
                item = random.choice(items)
                while item["price"] >= self.rest_of_value:
                    item = random.choice(items)
                self.rest_of_value -= item["price"]
                gp = random.randint(1, self.rest_of_value)
                self.rest_of_value -= gp
            else:
                if self.rest_of_value > lowest_price and only_item:
                    item = random.choice(items)
                    while item["price"] >= self.rest_of_value:
                        item = random.choice(items)
                    self.rest_of_value -= item["price"]
                else:
                    gp = random.randint(1, self.rest_of_value)
                    self.rest_of_value -= gp

        return {"item": item, "gp": gp}
        

    def roll_dice(self, number_of_dice: int, dice_size: int) -> int:
        """Function simulates a dice roll

        Args:
            number_of_dice (int): Number of dice to be thrown
            dice_size (int): Dice size

        Returns:
            int: Sum of rolled values
        """
        return sum(random.randint(1, dice_size) for _ in range(number_of_dice))
    

def calculate_party_level(average_player_level: int, number_of_players: int) -> int:
    party_level = average_player_level + math.floor((number_of_players - 4) / 2)
    if party_level < 1:
        party_level = 1
    elif party_level > 20:
        party_level = 20
    return party_level