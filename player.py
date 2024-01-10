class Player:

    def __init__(self, name: str, id_: int, hp: int, damage: int) -> None:
        self.name = name
        self.id = id_
        self.inventory = []
        self.hp = hp
        self.handcuffs = False
        self.damage = damage

    def inventory_str(self) -> str:
        inv = []
        for slot in range(len(self.inventory)):
            inv.append(f'{slot+1}. {self.inventory[slot]}')
        return '\n'.join(inv)
