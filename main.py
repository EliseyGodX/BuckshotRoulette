from threading import Thread
import time
from dotenv import load_dotenv
from os import getenv
import vk
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType 
from vk_api.utils import get_random_id
from vk_messages import *
from game import Game
from effects import Effects
from keyboards import Keyboard

load_dotenv()

TIME = 900
DELAY_TO_KICK = 90


def message(user_id, message, keyboard=None, delay=True) -> None: 
    if delay == True: time.sleep(1.2)
    if keyboard is None:
        vk.messages.send(   
            user_id=user_id,    
            message=message,    
            random_id=get_random_id(),   
            )
    else:  vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard(),
            message=message
        )

    


def session(first_id, first_name, second_id, second_name):
    def double_message(text: str) -> None:
        message(first_id, text, delay=False)
        message(second_id, text, delay=False)
        time.sleep(2.5)

    message(second_id, '🟨Вы садитесь за стол, ружьё лежит к вам стволом. Первым ходит противник🟨')
    message(first_id, '🟩Вы садитесь за стол, ружьё лежит к вам прикладом. Первый ход за вами🟩')
    game = Game(first_name, second_name, first_id, second_id)
    active = game.first
    passive = game.second
    msg_time = 0
    while active.hp > 0 and passive.hp > 0:
        if len(game.que) == 0: 
            game.new_item()
            game.new_que()
            double_message(f'❗❗❗Новый набор патрон! 🔴Боевых: {game.que.count(True)}🔴, ⚪Холостых: {game.que.count(False)}⚪❗❗❗')

        game.reset()
        double_message(f'''🔫Новый ход🔫
Ружьё у {active.name}

{active.name} стерпит ещё {active.hp}❤ пуль, {passive.name} - {passive.hp}❤

💼 На столе {active.name}: \n{active.inventory_str()}

💼 На столе {passive.name}: \n{passive.inventory_str()}''')
        flag = False
        while flag != True:
            message(active.id, f'🟩Ваш черёд. Будете использовать что либо?🟩\n{active.inventory_str()}',
                    keyboard=Keyboard.inventory(active))
            msg_time = time.time()
            for event in longpoll.listen():
                if time.time() - msg_time > DELAY_TO_KICK: 
                    double_message(f'🟨🟨🟨{active.name} проигрывает из-за афк!🟨🟨🟨')
                    admission[first_name] = time.time()
                    admission[second_name] = time.time()
                    return
                if (event.type ==  VkEventType.MESSAGE_NEW and event.to_me 
                    and event.from_user and event.user_id == active.id):
                    if event.message[0].isdigit() and 1 <= int(event.message[0]) <= 9:
                        try:
                            effect = active.inventory[int(event.message[0]) - 1]
                            if effect == '🔎 лупа': 
                                double_message(Effects.magnifier(active, game))
                            elif effect == '🚬 сигареты': 
                                if active.hp == game.max_hp:
                                    message(active.id, f'❤У вас максимальное количество хп, сигареты не помогут❤')
                                else: double_message(Effects.sigarets(active))
                            elif effect == '🍺 пиво': 
                                double_message(Effects.beer(active, game))
                            elif effect == '🔪 нож':
                                if active.damage != game.normal_damage: 
                                     message(active.id, f'🔫Ружьё уже обрезано🔫')
                                else: double_message(Effects.knife(active))
                            elif effect == '⛓️ наручники':
                                if passive.handcuffs is True:
                                    message(active.id, f'⛓️Противник уже связан⛓️') 
                                else: double_message(Effects.handcuffs(active, passive))
                        except: flag = True
                    elif event.message == '-': flag = True

                    break
        
        message(active.id, f'🟩В кого выстрелите? (/сдаться)🟩', keyboard=Keyboard.shot())
        msg_time = time.time()
        for event in longpoll.listen(): 
            if time.time() - msg_time > DELAY_TO_KICK: 
                double_message(f'🟨🟨🟨{active.name} проигрывает из-за афк!🟨🟨🟨')
                admission[first_name] = time.time()
                admission[second_name] = time.time()
                return
            if (event.type ==  VkEventType.MESSAGE_NEW and event.to_me 
                and event.from_user and event.user_id == active.id):
                if event.message == 'Противника': 
                    bullet = game.shot(active, passive)
                    double_message(f'{active.name} стреляет в {passive.name}🔫! Патрон оказывается {bullet}')
                    if passive.handcuffs != True:
                        passive_ = passive
                        passive = active
                        active = passive_
                    break 
                elif event.message == 'В СЕБЯ': 
                    bullet = game.shot(active, active)
                    double_message(f'{active.name} стреляет 🔫 в СЕБЯ! патрон оказывается {bullet}')
                    break
                elif event.message == '/сдаться':
                    double_message(f'🟨🟨🟨{active.name} сдаётся и преклоняет колено перед {passive.name}!🟨🟨🟨')
                    return

    if game.first.hp > 0: name = game.first.name
    else: name = game.second.name
    double_message(f'🟩🟩🟩{name} Отправил в противника 🔫 финальную пулю, и оказывается победителем!🟩🟩🟩')
    admission[first_name] = time.time()
    admission[second_name] = time.time()

        





def main():
    global admission
    lobby = {}
    admission = {}
    for event in longpoll.listen(): 
        if event.type ==  VkEventType.MESSAGE_NEW and event.to_me and event.from_user: 
            if event.message.lower().startswith('играть'):
                user_id = event.user_id
                user_get = vk.users.get(user_ids=(user_id), fields='screen_name')[0]
                screen_name = user_get['screen_name']
                
                if screen_name not in admission or time.time() - admission[screen_name] > TIME:
                    lobby[screen_name] = {
                        'id_': user_id,
                        'name': screen_name,
                        'private': False
                    }
                    if screen_name not in admission: admission[screen_name] = 0
                    try:
                        if event.message.split(' ')[1].lower() == 'приват': message(user_id, '👽Вы вошли в приватное лобби👽')
                        lobby[screen_name]['private'] = True
                    except: pass

                    lobby_ = [slot + '\n' for slot in lobby if lobby[slot]['private'] != True]
                    message(user_id, f'🟩Используйте Присоединиться <nick> для того, чтобы начать сессию.🟩 \nВ лобби: \n{"".join(lobby_)}')

                else: message(user_id, f'Между играми выдерживайте перерыв в 15 минут (ограничения вк). Вам осталось ждать: {TIME - admission[user_id] - time.time()} секунд')

            elif event.message.lower().startswith('присоединиться'):
                user_id = event.user_id
                user_get = vk.users.get(user_ids=(user_id), fields='screen_name')[0]
                screen_name = user_get['screen_name']
                if str(event.message).split(' ')[1] in lobby and str(event.message).split(' ')[1] != screen_name:
                    first_id = lobby[event.message.split(' ')[1]]['id_']
                    first_name = lobby[event.message.split(' ')[1]]['name']

                    if screen_name in admission and time.time() - admission[screen_name] > TIME and time.time() - admission[first_name] > TIME:
                        lobby.pop(first_name)
                        try: lobby.pop(screen_name)
                        except: pass
                        th = Thread(target=session, args=(first_id, first_name, user_id, screen_name, ))
                        th.start()

                else: message(user_id, 'Некорректное имя')

if __name__ == '__main__': 
    vk_session = vk_api.VkApi(token=getenv("TOKEN"))  
    longpoll = VkLongPoll(vk_session)   
    vk = vk_session.get_api()   
    main()
    