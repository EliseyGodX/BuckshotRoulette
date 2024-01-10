import random

class Effects:

    def magnifier(player: object, game: object) -> str:
        if game.que[0] is True: bullet = '🔴БОЕВОЙ🔴'
        else: bullet = '⚪ХОЛОСТОЙ⚪'
        (player.inventory).remove('🔎 лупа')
        return f'🔎{player.name}🔎 использует лупу, и обнаруживает, что следующий патрон {bullet}'
    
    def sigarets(player: object) -> str:
        player.hp += 1
        (player.inventory).remove('🚬 сигареты')
        return f'🚬{player.name}🚬 затягивает сигарету и восстанавливает себе одно хп'
    
    def beer(player: object, game: object) -> str:
        random.shuffle(game.que)
        if game.que.pop(0) is True: bullet = '🔴БОЕВОЙ🔴'
        else: bullet = '⚪ХОЛОСТОЙ⚪'
        (player.inventory).remove('🍺 пиво')
        return f'🍺{player.name}🍺 выпивает банку крепкого и случайным образом перезаряжает ружьё, выранив при этом {bullet} патрон'
    
    def knife(player: object) -> str:
        player.damage += player.damage
        (player.inventory).remove('🔪 нож')
        return f'🔪{player.name}🔪 обрезает ствол и получает обрез с ДВОЙНЫМ УРОНОМ!!!'
    
    def handcuffs(player: object, contender: object) -> str:
        contender.handcuffs = True
        (player.inventory).remove('⛓️ наручники')
        return f'⛓️{player.name}⛓️ сковывает соперника наручниками и получает возможность сделать 2 выстрела'
