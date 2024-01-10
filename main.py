import asyncio
from dotenv import load_dotenv
from os import getenv
import vk
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType 
from vk_messages import *
from loguru import logger
from game import Game
from effects import Effects

load_dotenv()

vk_session = vk_api.VkApi(token=getenv("TOKEN"))  
longpoll = VkLongPoll(vk_session)   
vk = vk_session.get_api()   

def message(user_id, message): 
    vk.messages.send(   
        user_id=user_id,    
        message=message,    
        random_id=0,   
        )
    


async def session(first_id, first_name, second_id, second_name):
    def double_message(text: str) -> None:
        message(first_id, text)
        message(second_id, text)

    message(first_id, 'Вы садитесь за стол, ружьё лежит к вам прикладом. Первый ход за вами')
    message(second_id, 'Вы садитесь за стол, ружьё лежит к вам стволом. Первым ходит противник')
    game = Game(first_name, second_name, first_id, second_id)
    active = game.first
    passive = game.second
    while active.hp > 0 or passive.hp > 0:
        if len(game.que) == 0: 
            game.new_item()
            game.new_que()
            double_message(f'Новый набор патрон! Боевых: {game.que.count(True)}, Холостых: {game.que.count(False)}')

        game.reset()
        double_message(f'''---Новый ход---
Ружьё у {active.name}
{active.name} стерпит ещё {active.hp} пуль, {passive.name} - {passive.hp}

На столе {active.name}: \n{active.inventory_str()}

На столе {passive.name}: \n{passive.inventory_str()}''')
        
        message(active.id, f'Ваш черёд. Будете использовать что либо?\n{active.inventory_str}')
        for event in longpoll.listen(): 
            if (event.type ==  VkEventType.MESSAGE_NEW and event.to_me 
                and event.from_user and event.user_id == active.id):
                if event.message in ['1', '2', '3', '4', '5', '6', '7', '8', '9']:
                    try:
                        effect = active.inventory[int(event.message) + 1]
                        if effect == 'magnifier': 
                            double_message(active, Effects.magnifier(active, game))
                        elif effect == 'sigarets': 
                            double_message(Effects.sigarets(active))
                        elif effect == 'beer': 
                            double_message(Effects.beer(active, game))
                        elif effect == 'knife': 
                            double_message(Effects.knife(active))
                        elif effect == 'handcuffs': 
                            double_message(Effects.handcuffs(active, passive))
                    except: pass
        
        message(active.id, f'В кого выстрелите (0 - себя, 1 - противника)?')
        for event in longpoll.listen(): 
            if (event.type ==  VkEventType.MESSAGE_NEW and event.to_me 
                and event.from_user and event.user_id == active.id):
                if event.message == '1': 
                    bullet = game.shot(active, passive)
                    double_message(f'{active.name} стреляет в {passive.name}! патрон оказывается {bullet}')
                    if passive.handcuffs != True:
                        passive_ = active
                        passive = active
                        passive = passive_ 
                else: 
                    game.shot(active, active)
                    double_message(f'{active.name} стреляет в СЕБЯ! патрон оказывается {bullet}')

    if game.first.hp > 0: name = game.first.hp
    else: name = game.second.hp
    double_message(f'{name} Отправил в противника финальную пулю, и оказывается победителем!')
                 

        





if __name__ == '__main__':
    lobby = {}
    for event in longpoll.listen(): 
        if event.type ==  VkEventType.MESSAGE_NEW and event.to_me and event.from_user: 
            if event.message == 'Играть':
                user_id = event.user_id
                user_get = vk.users.get(user_ids=(user_id), fields='screen_name')[0]
                screen_name = user_get['screen_name']
                lobby[screen_name] = [user_id, screen_name]
                message(user_id, lobby.keys())

            elif event.message.startswith('Присоединиться'):
                user_id = event.user_id
                user_get = vk.users.get(user_ids=(user_id), fields='screen_name')[0]
                screen_name = user_get['screen_name']
                if str(event.message).split(' ')[1] in lobby:
                    first_id = lobby[str(event.message).split(' ')[1]][0]
                    first_name = lobby[str(event.message).split(' ')[1]][1]
                    lobby.pop(str(event.message).split(' ')[1])
                    try: lobby.pop(screen_name)
                    except: pass
                    asyncio.run(session(first_id, first_name, user_id, screen_name))

                        