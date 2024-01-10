import random

class Effects:

    def magnifier(player: object, game: object) -> str:
        if game.que[0] is True: bullet = 'БОЕВОЙ'
        else: bullet = 'ХОЛОСТОЙ'
        (player.inventory).remove('magnifier')
        return f'{player.name} использует лупу, и обнаруживает, что следующий патрон {bullet}'
    
    def sigarets(player: object) -> str:
        player.hp += 1
        (player.inventory).remove('sigarets')
        return f'{player.name} затягивает сигарету и восстанавливает себе одно хп'
    
    def beer(player: object, game: object) -> str:
        random.shuffle(game.que)
        if game.que[0] is True: bullet = 'БОЕВОЙ'
        else: bullet = 'ХОЛОСТОЙ'
        game.que.pop(0)
        (player.inventory).remove('beer')
        return f'{player.name} выпивает банку крепкого и случайным образом перезаряжает ружьё, выранив при этом {bullet} патрон'
    
    def knife(player: object) -> str:
        player.damage += player.damage
        (player.inventory).remove('knife')
        return f'{player.name} обрезает ствол и получает обрез с двойным уроном'
    
    def handcuffs(player: object, contender: object) -> str:
        contender.handcuffs = True
        (player.inventory).remove('handcuffs')
        return f'{player.name} сковывает соперника наручниками и получает возможность сделать 2 выстрела'
