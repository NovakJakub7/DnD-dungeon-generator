DROP TABLE IF EXISTS monsters;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;

CREATE TABLE monsters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  monster_name TEXT UNIQUE NOT NULL,
  size TEXT NOT NULL,
  monster_type TEXT NOT NULL,
  motif TEXT NOT NULL,
  challenge_rating INTEGER NOT NULL
);

CREATE TABLE items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_name TEXT UNIQUE NOT NULL,
  item_type TEXT NOT NULL,
  weight TEXT DEFAULT '0',
  price INTEGER NOT NULL
) ;

CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
) ;

INSERT INTO monsters(monster_name, size, monster_type, motif, challenge_rating) VALUES
('Allip', 'Medium', 'Undead', 'Abandoned', 3),
('Human Warrior Skeleton', 'Medium', 'Undead', 'Abandoned', 1),
('Ghoul', 'Medium', 'Undead', 'Abandoned', 1),
('Goblin', 'Small', 'Humanoid', 'Abandoned', 1),
('Hobgoblin', 'Medium', 'Humanoid', 'Abandoned', 1),
('Clay Golem', 'Large', 'Construct', 'Abandoned', 10),
('Ogre', 'Large', 'Giant', 'Abandoned', 3),
('Ogre, 4th-level Barbarian', 'Large', 'Giant', 'Abandoned', 7),
('Monstrous Scorpion', 'Small', 'Vermin', 'Vermin', 1),
('Bat Swarm', 'Small', 'Animal', 'Vermin', 2),
('Monstrous Spider', 'Medium', 'Vermin', 'Vermin', 1),
('Giant Ant, Soldier', 'Medium', 'Vermin', 'Vermin', 2),
('Giant Ant, Queen', 'Large', 'Vermin', 'Vermin', 2),
('Monstrous Centipede', 'Large', 'Vermin', 'Vermin', 1),
('Minotaur', 'Large', 'Monstrous Human', 'Underdark', 4),
('Dread Wraith', 'Large', 'Undead', 'Underdark', 11),
('Troll', 'Large', 'Giant', 'Underdark', 5),
('Troglodyte', 'Medium', 'Humanoid', 'Underdark', 1),
('Duergar', 'Medium', 'Humanoid', 'Underdark', 1),
('Dire Rat', 'Small', 'Animal', 'Underdark', 1);

INSERT INTO items(item_name, item_type, weight, price) VALUES
('Leather Armor', 'Armor', '15 lb', 10),
('Chain Shirt', 'Armor', '25 lb', 100),
('Chainmail', 'Armor', '40 lb', 150),
('Breastplate', 'Armor', '30 lb', 200),
('Half-plate', 'Armor', '50 lb', 600),
('Full-plate', 'Armor', '50 lb', 1500),
('Buckler', 'Shield', '5 lb', 15),
('Light Steel Shield', 'Shield', '6 lb', 9),
('Heavy Wooden Shield', 'Shield', '10 lb', 7),
('Heavy Steel Shield', 'Shield', '15 lb', 20),
('Dagger', 'Weapon', '1 lb', 2),
('Sickle', 'Weapon', '2 lb', 6),
('Mace', 'Weapon', '8 lb', 12),
('Spear', 'Weapon', '6 lb', 2),
('Crossbow', 'Weapon', '8 lb', 50),
('Battleaxe', 'Weapon', '6 lb', 10),
('Warhammer', 'Weapon', '5 lb', 12),
('Greatsword', 'Weapon', '8 lb', 50),
('Invisibility Ring', 'Ring', '1 lb', 20000),
('Protection Ring', 'Ring', '1 lb', 2000),
('Fire Staff', 'Staff', '1 lb', 28500),
('Healing Staff', 'Staff', '1 lb', 27750),
('Amulet of Health', 'Wondrous Item', '1 lb', 4000),
('Boots of Speed', 'Wondrous Item', '1 lb', 12000),
('Mace of Blood', 'Cursed Item', '8 lb', 16000),
('Berserking Sword', 'Cursed Item', '8 lb', 17500);