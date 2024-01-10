import json
import random
from player import Player

with open('settings.json', encoding='utf-8') as f:
    SETTINGS = json.load(f)

effects = ['magnifier', 'sigarets', 'beer', 'knife', 'handcuffs']

class Game:

    def __init__(self, name1: str, name2: str, id1: int, id2: int,
                 hp = SETTINGS['hp'], damage = SETTINGS['damage'],
                 inventory_size = SETTINGS['inventory_size'], 
                 que_size = SETTINGS['que_size']) -> None: 
        self.first = Player(name1, id1, hp, damage)
        self.second = Player(name2, id2, hp, damage)
        self.normal_damage = damage
        self.inventory_size = inventory_size
        self.que_size = que_size
        self.que = []


    def new_item(self) -> None:
        for _ in range(3):
            self.first.inventory.append(random.choice(effects))
            self.second.inventory.append(random.choice(effects))

        if len(self.first.inventory) > self.inventory_size:
            while len(self.first.inventory) != self.inventory_size: 
                self.first.inventory.pop(0)

        if len(self.second.inventory) > self.inventory_size:
            while len(self.second.inventory) != self.inventory_size: 
                self.second.inventory.pop(0)


    def new_que(self) -> None:
        live_bullet = random.randint(1, self.que_size - 2)
        blank_bullet = random.randint(2, self.que_size - live_bullet)
        self.que = [True] * live_bullet + [False] * blank_bullet
        random.shuffle(self.que)

    def reset(self) -> None:
        self.first.damage = self.normal_damage
        self.second.damage = self.normal_damage
        self.first.handcuffs = False
        self.second.handcuffs = False

    def shot(self, shooter: object, victim: object) -> str:
        if self.que[0] == True:
            victim.hp -= shooter.damage
            return 'БОЕВЫМ'
        else: return 'ХОЛОСТЫМ'
        
