from threading import Thread
from queue import Queue
import time
import random
import sqlite3
from dotenv import load_dotenv
from os import getenv
import vk
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType 
from vk_api.utils import get_random_id
from vk_messages import *
from loguru import logger
from game import Game
from effects import Effects
from keyboards import Keyboard

load_dotenv()

TIME = 120
DELAY_TO_KICK = 90
SEASON = 0
WINNING_RAITING = 35
LOSERS_PERCENTAGE = 0.65

logger.add('logger.log', format='{time} ||{message}', 
           rotation='2 MB', enqueue=True)

def message(user_id, message, keyboard=None, delay=True) -> None: 
    if delay == True: time.sleep(0.6)
    if keyboard is None:
        vk.messages.send(   
            user_id=user_id,    
            message=message,    
            random_id=get_random_id(),   
            )
    else: vk.messages.send(
            user_id=user_id,
            random_id=get_random_id(),
            keyboard=keyboard.get_keyboard(),
            message=message
        )

    

def leaderboard():    
    leaderboard_db = sqlite3.connect('leaderboard.db')
    cursor = leaderboard_db.cursor()

    while True:  # id, name, raiting, victories, defeats
        if db_queue.empty() != True:
            data = db_queue.get()
            
            if data['command'] == 'fight':                                                      
                winner = cursor.execute(f'''SELECT * FROM Season{SEASON}                        
                            WHERE id = (?)''', (data['winner']['id'], )).fetchone()          
                looser = cursor.execute(f'''SELECT * FROM Season{SEASON} 
                            WHERE id = (?)''', (data['looser']['id'], )).fetchone()
                
                if winner is None:
                    winner = [data['winner']['id'], data['winner']['name'], 100, 0, 0]
                    cursor.execute(f'''INSERT INTO Season{SEASON} (id, name, raiting, victories, defeats) 
                                    VALUES (?, ?, ?, ?, ?)''', (tuple(winner)))
                if looser is None:
                    looser = [data['looser']['id'], data['looser']['name'], 100, 0, 0]
                    cursor.execute(f'''INSERT INTO Season{SEASON} (id, name, raiting, victories, defeats) 
                                    VALUES (?, ?, ?, ?, ?)''', (tuple(looser)))
                    
                looser = [x for x in looser]
                winner = [x for x in winner]

                winner_rat = winner[2]
                looser_rat = looser[2]


                winner[2] += int(WINNING_RAITING * (looser[2] / winner[2]))
                looser[2] -= int(WINNING_RAITING * LOSERS_PERCENTAGE * (looser[2] / winner[2]))
                winner[3] += 1
                looser[4] += 1

                cursor.execute(f'''UPDATE Season{SEASON} SET raiting=?, victories=?, defeats=? 
                                    WHERE id=?''', (winner[2], winner[3], winner[4], winner[0]))
                cursor.execute(f'''UPDATE Season{SEASON} SET raiting=?, victories=?, defeats=? 
                                    WHERE id=?''', (looser[2], looser[3], looser[4], looser[0]))
                leaderboard_db.commit()

                logger.debug(f'WINNER: {winner[0]} - {winner_rat}-->{winner[2]}; LOOSER: {looser[0]} - {looser_rat}-->{looser[2]}')

                message(winner[0], f'''Поздравляем с победой!
Ваш текущий рейтинг: {winner[2]} (было: {winner_rat})
Ваша статистика (победы/поражения): {winner[3]}/{winner[4]}
''')
                message(looser[0], f'''Повезёт в следующий раз :(
Ваш текущий рейтинг: {looser[2]} (было: {looser_rat})
Ваша статистика (победы/поражения): {looser[3]}/{looser[4]}
''')            
            
                            
            elif data['command'] == 'top':
                query = cursor.execute(f"SELECT * FROM Season{SEASON} ORDER BY raiting DESC LIMIT 10").fetchall()
                statistics = 'LEADERBOARD\n'
                for i in range(len(query)):
                    statistics += f'{i+1}. {query[i][1]}  --{query[i][2]}--  {query[i][3]}/{query[i][4]}\n'
                message(data['id'], statistics)


            elif data['command'] == 'raiting':
                query = cursor.execute(f'''SELECT * FROM Season{SEASON}                        
                            WHERE name = (?)''', (data['name'], )).fetchone()
                if query is None: message(data['id'], 'Игрок не найден')
                else: 
                    message(data['id'], f'{query[1]}  --{query[2]}--  {query[3]}/{query[4]}')


def session(first_id, first_name, second_id, second_name):
    def double_message(text: str) -> None:
        message(first_id, text, delay=False)
        message(second_id, text, delay=False)
        time.sleep(2.5)

    def session_state(winner, looser) -> None:
        admission[winner.id] = time.time()
        admission[looser.id] = time.time()
        db_queue.put({'command': 'fight',
        "winner": {
            "id": winner.id,
            "name": winner.name
        },
        "looser": {
            "id": looser.id,
            "name": looser.name 
        }})

    count = [False, False]
    time_ = time.time()
    message(second_id, f'🟨Ожидаем ответа от {first_name}🟨', keyboard=Keyboard.session())
    message(first_id, f'🟩Найдена сессия с {second_name}!🟩', keyboard=Keyboard.session())
    while count != [True, True]:
        for event in longpoll.listen():
            if time.time() - time_ > DELAY_TO_KICK:
                double_message('Время вышло, сессия была завершена без изменения статистики')
                return 
            if (event.type ==  VkEventType.MESSAGE_NEW and event.to_me 
                    and event.from_user):
                if event.user_id == first_id and event.message == 'Начать игру':
                    count[0] = True
                    message(first_id, 'Вы подключены к сесси, ожидаем соперника')
                    break
                elif event.user_id == second_id and event.message == 'Начать игру':
                    count[1] = True
                    message(second_id, 'Вы подключены к сесси, ожидаем соперника')
                    break
                elif (event.user_id == first_id or event.user_id == second_id) and event.message == 'Покинуть сессию':
                    double_message('Один из участников сессии отказался от участия, сессия была завершена без изменения статистики')
                    return
                
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
                    session_state(passive, active)
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
                                if len(game.que) == 1: message(active.id, 'В очереди только 1 патрон')
                                else: double_message(Effects.beer(active, game))
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
                session_state(passive, active)
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
                    session_state(passive, active)
                    return

    if game.first.hp > 0: 
        winner = game.first
        looser = game.second
    else: 
        winner = game.second
        looser = game.first
    double_message(f'🟩🟩🟩{winner.name} Отправил в противника 🔫 финальную пулю, и оказывается победителем!🟩🟩🟩')
    session_state(winner, looser)
        





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
                
                if user_id not in admission or time.time() - admission[user_id] > TIME:
                    lobby[screen_name] = {
                        'id_': user_id,
                        'name': screen_name,
                        'private': False
                    }
                    if user_id not in admission: admission[user_id] = 0
                    try:
                        if event.message.split(' ')[1].lower() == 'приват': message(user_id, f'👽Вы вошли в приватное лобби. Ваш ник для подключения: {screen_name}👽')
                        lobby[screen_name]['private'] = True
                    except: pass

                    lobby_ = [slot + '\n' for slot in lobby if lobby[slot]['private'] != True]
                    message(user_id, f'🟩Используйте Присоединиться <nick> для того, чтобы начать сессию.🟩 \nВ лобби: \n{"".join(lobby_)}', keyboard=Keyboard.lobby())

                else: message(user_id, f'Между играми выдерживайте перерыв в {TIME} секунды (ограничения вк). Вам осталось ждать: {int(TIME - time.time() + admission[user_id])} секунд')

            elif event.message.lower().startswith('присоединиться') and len(str(event.message.lower()).split(' ')) != 1:
                user_id = event.user_id
                user_get = vk.users.get(user_ids=(user_id), fields='screen_name')[0]
                screen_name = user_get['screen_name']
                if str(event.message).split(' ')[1] in lobby and str(event.message).split(' ')[1] != screen_name:
                    first_id = lobby[event.message.split(' ')[1]]['id_']
                    first_name = lobby[event.message.split(' ')[1]]['name']

                    if user_id in admission and time.time() - admission[user_id] > TIME and time.time() - admission[first_id] > TIME:
                        lobby.pop(first_name)
                        try: lobby.pop(screen_name)
                        except: pass
                        th = Thread(target=session, args=(first_id, first_name, user_id, screen_name, ))
                        th.start()

                else: message(user_id, 'Некорректное имя', keyboard=Keyboard.lobby())

            elif event.message.lower() == 'случайная сессия':
                user_id = event.user_id
                user_get = vk.users.get(user_ids=(user_id), fields='screen_name')[0]
                screen_name = user_get['screen_name']
                lobby_ = [slot for slot in lobby if lobby[slot]['private'] != True and lobby[slot]['name'] != screen_name]
                if len(lobby_) > 0 and screen_name in lobby:
                    first_name = random.choice(lobby_)
                    first_id = lobby[first_name]['id_']
                    if user_id in admission and time.time() - admission[user_id] > TIME and time.time() - admission[first_id] > TIME:
                        lobby.pop(first_name)
                        try: lobby.pop(screen_name)
                        except: pass
                        th = Thread(target=session, args=(first_id, first_name, user_id, screen_name, ))
                        th.start()
                else: message(user_id, 'Войдите в лобби или лобби пустое, подождите следующего игрока', keyboard=Keyboard.lobby())

            elif event.message.lower() == 'покинуть лобби':
                user_id = event.user_id
                user_get = vk.users.get(user_ids=(user_id), fields='screen_name')[0]
                screen_name = user_get['screen_name']
                if screen_name in lobby:
                    lobby.pop(screen_name)
                    message(user_id, 'Вы вышли из лобби')

            elif event.message.lower() == 'начало': 
                message(event.user_id, 'Используйте команду "играть". \nОзнакомьтесь с правилами: https://vk.com/buckshotroulettebot?w=wall-224193723_1')


            elif event.message.lower() == 'топ':
                db_queue.put({'command': 'top', 'id': event.user_id})

            
            elif event.message.lower().startswith('рейтинг'):
                try: name = event.message.split(' ')[1].lower()
                except: name = vk.users.get(user_ids=(event.user_id), fields='screen_name')[0]['screen_name']
                finally: db_queue.put({'command': 'raiting', 'name': name, 'id': event.user_id})

if __name__ == '__main__': 
    vk_session = vk_api.VkApi(token=getenv("TOKEN"))  
    longpoll = VkLongPoll(vk_session)   
    vk = vk_session.get_api()

    db_queue = Queue()
    db_thread = Thread(target=leaderboard, args=())
    db_thread.start()

    main()
    