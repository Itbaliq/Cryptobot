import sqlite3
import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import threading
import requests
from datetime import datetime
from pytz import timezone

TEST_TIME=86400
TOKEN=''

admin_id=[514503717]
lock = threading .Lock()
conn = sqlite3.connect('db/database.db', check_same_thread=False)
cursor = conn.cursor()
conn_prc = sqlite3.connect('db/process.db', check_same_thread=False)
cursor_prc = conn_prc.cursor()
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class Form(StatesGroup):
    name = State()

button_back_to_main_menu = types.InlineKeyboardButton('🔙Назад', callback_data='main_menu')
button_back_to_main_menu2 = types.InlineKeyboardButton('🔙 Menu', callback_data='back_menu')
keyboard_back=types.InlineKeyboardMarkup().add(button_back_to_main_menu2)
button_test = types.InlineKeyboardButton('Test', callback_data='test')
async def TakeMenuId(call):
    menu=conn.execute("SELECT * FROM test WHERE user_id='" + str(call.from_user.id) + "'")
    menu=menu.fetchall()[0]
    return menu[5],menu[4],menu[0],menu[1],menu[2],menu[3]
async def set_registration(call):
    user_id = call.from_user.id
    user_name = call.from_user.first_name
    username = call.from_user.username
    cursor.execute('INSERT INTO test (user_id, user_name, username) VALUES (?, ?, ?)', (user_id, user_name, username))
    conn.commit()
    for n in admin_id:
        if user_id!=n:
            text=f"New\n\nID: <code>{user_id}</code>\nNAME: <code>{user_name}</code>\nUSERNAME:   @{username}"
            text+=f"\nLINK: <a href='tg://user?id={call.from_user.id}'>LINK</a> "
            try:
                await bot.send_message(n, text=text,parse_mode="HTML")
            except:
                print(f"ERROR")
async def send_code_error(message):
    menu_ids=await TakeMenuId(message)
    keyboards = types.InlineKeyboardMarkup()
    main_text=f"❌ERROR❌\n/start"
    try:
        await bot.send_message(chat_id=menu_ids[0], text=main_text,reply_markup=keyboards,parse_mode="HTML")
    except:
        print(f"ERROR")
async def coin_info_req(coin):
    url=f"https://data.messari.io/api/v1/assets/{coin}/metrics"
    req=requests.get(url)
    res=req.json()
    market_data=res["data"]["market_data"]
    ohlcv_last_1_hour=market_data["ohlcv_last_1_hour"]
    ohlcv_last_24_hour=market_data["ohlcv_last_24_hour"]
    tz=timezone('Europe/Moscow')
    now = datetime.now(tz).strftime('%Y-%m-%d %H:%M')
    text=f"🪙 <b>{coin.upper()}</b>\n"
    text+=f"Time: {now}\n"
    text+=f"\nprice_usd: {round(market_data['price_usd'],3)} $"
    text+=f"\npercent_change_usd_last_1_hour: {round(market_data['percent_change_usd_last_1_hour'],5)} %"
    text+=f"\npercent_change_usd_last_24_hours: {round(market_data['percent_change_usd_last_24_hours'],5)} %"
    text+=f"\n\nLast 1 hour info:"
    text+=f"\n  open: {round(ohlcv_last_1_hour['open'],3)} $"
    text+=f"\n  high: {round(ohlcv_last_1_hour['high'],3)} $"
    text+=f"\n  low: {round(ohlcv_last_1_hour['low'],3)} $"
    text+=f"\n  close: {round(ohlcv_last_1_hour['close'],3)} $"
    #text+=f"\n  volume: {round(ohlcv_last_1_hour['volume'],3)} $"
    text+=f"\n\nLast 24 hours info:"
    text+=f"\n  open: {round(ohlcv_last_24_hour['open'],3)} $"
    text+=f"\n  high: {round(ohlcv_last_24_hour['high'],3)} $"
    text+=f"\n  low: {round(ohlcv_last_24_hour['low'],3)} $"
    text+=f"\n  close: {round(ohlcv_last_24_hour['close'],3)} $"
    #text+=f"\n  volume: {round(ohlcv_last_24_hour['volume'],3)} $"
    return(text,market_data)
async def coin_info(call):
    menu_ids=await TakeMenuId(call)
    keyboard = types.InlineKeyboardMarkup()
    coin=call.data.replace('coin_', '')
    text ,market_data=await coin_info_req(coin)
    button_refresh=types.InlineKeyboardButton(text="Обновить", callback_data=f'coin_{coin}')
    keyboard.add(button_refresh)
    button_coins_back = types.InlineKeyboardButton(text="🔙Назад", callback_data=f'coins')
    keyboard.add(button_coins_back)
    try:
        await bot.edit_message_text(chat_id=menu_ids[0], message_id=menu_ids[1],reply_markup=keyboard, text=text, parse_mode="HTML")
    except:
        print(f"ERROR")
async def check_profile(call):
    cursor.execute("SELECT user_id FROM test WHERE user_id='" + str(call.from_user.id) + "'")
    res = cursor.fetchone()
    if not res:
        await start_main_menu(call)
        return False
    return True
async def coins(call):
    menu_ids=await TakeMenuId(call)
    coins=["btc","eth","usdt","bnb","ltc","doge","trx","dai","xmr","xtz"]
    text=f"{await get_name(call.from_user.first_name,call.from_user.last_name)}, выбери валюту и бот даст информацию"
    keyboard = types.InlineKeyboardMarkup()
    for n in coins:
        button_text=n.upper()
        button = types.InlineKeyboardButton(text=button_text, callback_data=f'coin_{n}')
        keyboard.add(button)
    keyboard.add(button_back_to_main_menu2)     
    try:
        await bot.edit_message_text(chat_id=menu_ids[0], message_id=menu_ids[1],reply_markup=keyboard, text=text)
    except:
        print(f"ERROR")
async def watch(call):
    menu_ids=await TakeMenuId(call)
    coins=["btc","eth","usdt","bnb","ltc","doge","trx","dai","xmr","xtz"]
    text=f"Каждые 10 секунд будет приходить сообщение в случае изменение курс на 1%"
    keyboard = types.InlineKeyboardMarkup()
    for n in coins:
        try:
            lock.acquire(True)
            cursor_prc.execute(f"SELECT author_id FROM  process WHERE author_id='{call.from_user.id}' AND coin='{n}'")
            res = cursor_prc.fetchone()
        finally:
            lock.release()  
        if not res:
            button_text=n.upper()
            button = types.InlineKeyboardButton(text=button_text, callback_data=f'watch_{n}')
            keyboard.add(button)
    keyboard.add(button_back_to_main_menu2)     
    try:
        await bot.edit_message_text(chat_id=menu_ids[0], message_id=menu_ids[1],reply_markup=keyboard, text=text)
    except:
        print(f"ERROR")
async def watch_set(call):
    coin=call.data.replace('watch_', '')
    try:
        lock.acquire(True)
        cursor_prc.execute(f"SELECT author_id FROM  process WHERE author_id='{call.from_user.id}' AND coin='{coin}'")
        res = cursor_prc.fetchone()
    finally:
        lock.release()  
    if not res:
        user_id = call.from_user.id
        cursor_prc.execute('INSERT INTO process (author_id, coin) VALUES (?, ?)', (user_id, coin))
        conn_prc.commit()
async def watch_start(call):
    menu_ids=await TakeMenuId(call)
    coin=call.data.replace('watch_', '')
    while True:
        await asyncio.sleep(10)
        try:
            lock.acquire(True)
            cursor_prc.execute(f"SELECT author_id FROM  process WHERE author_id='{call.from_user.id}' AND coin='{coin}'")
            res = cursor_prc.fetchone()
        finally:
            lock.release()  
        if res:
            text ,market_data=await coin_info_req(coin)
            if(abs(round(market_data['percent_change_usd_last_1_hour'],5))>1):
                keyboard = types.InlineKeyboardMarkup()
                button_stop = types.InlineKeyboardButton(text="STOP", callback_data=f'stop_{coin}')
                keyboard.add(button_stop)
                try:
                    await bot.send_message(chat_id=menu_ids[0], text=text,reply_markup=keyboard,parse_mode="HTML")
                except:
                    print(f"ERROR")
            else:
                print(f"{coin} {round(market_data['percent_change_usd_last_1_hour'],5)} %")
        else:
            print(f"IT WAS STOPPED EARLIER {coin}")
            break
async def stop(call):
    menu_ids=await TakeMenuId(call)
    coins=["btc","eth","usdt","bnb","ltc","doge","trx","dai","xmr","xtz"]
    text=f"Остановить слежку"
    keyboard = types.InlineKeyboardMarkup()
    for n in coins:
        try:
            lock.acquire(True)
            cursor_prc.execute(f"SELECT author_id FROM  process WHERE author_id='{call.from_user.id}' AND coin='{n}'")
            res = cursor_prc.fetchone()
        finally:
            lock.release()  
        if res:
            button_text=n.upper()
            button = types.InlineKeyboardButton(text=button_text, callback_data=f'stop_{n}')
            keyboard.add(button)
    keyboard.add(button_back_to_main_menu2)     
    try:
        await bot.edit_message_text(chat_id=menu_ids[0], message_id=menu_ids[1],reply_markup=keyboard, text=text)
    except:
        print(f"ERROR")
async def stop_coin(call):
    menu_ids=await TakeMenuId(call)
    coin=call.data.replace('stop_', '')
    try:
        cursor_prc.execute(f"DELETE FROM  process WHERE author_id='{call.from_user.id}' AND coin='{coin}'")
        conn_prc.commit()
    except:
        print("ERROR DELETE EMPTY LOTTERY")
async def get_name(first_name,last_name):
    name=""
    if(first_name!=None):
        name+=f" {first_name}"
    if(last_name!=None):
        name+=f" {last_name}"
    if(first_name==None) and (last_name==None):
        name+=" Anonymous"
    return name
async def start_main_menu(call):
    cursor.execute("SELECT user_id FROM test WHERE user_id='" + str(call.from_user.id) + "'")
    res = cursor.fetchone()
    if not res:
        await set_registration(call)
    else:
        chat_id=cursor.execute("SELECT menu_chat_id FROM test WHERE user_id='" + str(call.from_user.id) + "'").fetchone()[0]
        message_id=cursor.execute("SELECT menu_message_id FROM test WHERE user_id='" + str(call.from_user.id) + "'").fetchone()[0]
        if chat_id!=0 and message_id!=0:
            try:
                lock.acquire(True)
                cursor.execute("UPDATE test SET menu_chat_id = '0' WHERE user_id='" + str(call.from_user.id) + "'")
                cursor.execute("UPDATE test SET menu_message_id = '0' WHERE user_id='" + str(call.from_user.id) + "'")
                conn.commit()
                try:
                    await bot.delete_message(chat_id=chat_id,message_id=message_id)
                except:
                    print("ERROR CANT DELETE MSG")
            finally:
                lock.release()
    keyboard = types.InlineKeyboardMarkup()
    button_coins = types.InlineKeyboardButton(text="Курс криптовалют", callback_data=f'coins')
    button_watch = types.InlineKeyboardButton(text="Отслеживать курс", callback_data=f'watch')
    button_stop = types.InlineKeyboardButton(text="Остановить слежку", callback_data=f'stop')
    button_info = types.InlineKeyboardButton(text="Ответы на вопросы", callback_data=f'info')
    text=f"Привет,{await get_name(call.from_user.first_name,call.from_user.last_name)}"
    text+="\n\nМои контакты - @bubba1983"
    keyboard.add(button_coins)
    keyboard.add(button_watch)
    keyboard.add(button_stop)
    keyboard.add(button_info)
    try:
        main_message=await bot.send_message(call.from_user.id, text=text, reply_markup=keyboard, parse_mode="HTML")
        cursor.execute("UPDATE test SET menu_chat_id = '"+str(main_message.chat.id)+"' WHERE user_id='" + str(call.from_user.id) + "'")
        cursor.execute("UPDATE test SET menu_message_id = '"+str(main_message.message_id)+"' WHERE user_id='" + str(call.from_user.id) + "'")
        conn.commit()
    except:
        print(f"ERROR BOY WENT OUT {call.from_user.id}")
async def info(call):
    menu_ids=await TakeMenuId(call)
    text=f"Ответы на вопросы:\n"
    text+=f"\n1)Определить собственные движения цены фьючерса ETHUSDT, исключив из них движения вызванные влиянием цены BTCUSDT\n"
    text+=f"\nЯ не сильно сведущ в подобных вопросах ,но вот некоторые варианты ,которые мне удалось собрать"
    text+=f"\n\n1. Корреляционный анализ. Можно проанализировать корреляцию между ценами ETHUSDT и BTCUSDT на различных временных интервалах и выделить периоды, когда корреляция была наиболее низкой. В эти периоды можно предположить, что движения цены ETHUSDT были вызваны другими факторами, отличными от изменения цены BTCUSDT."
    text+=f"\n\n2. Факторный анализ. Можно выделить факторы, которые могут оказывать наибольшее влияние на цену ETHUSDT (например, новости из мира криптовалют, технические индикаторы и т.д.) и построить модель, которая будет учитывать влияние этих факторов на цену. При этом можно исключить из модели фактор изменения цены BTCUSDT."
    text+=f"\n\n3. Регрессионный анализ. Можно построить регрессионную модель, в которой зависимая переменная будет цена ETHUSDT, а независимыми переменными - факторы, которые могут оказывать влияние на цену. При этом можно исключить из модели фактор изменения цены BTCUSDT."
    text+=f"\n\nКакой подход будет наиболее эффективным зависит от конкретной ситуации и доступных данных."
    text+=f"\n\n2)Данные приходят с API одной крупной криптобиржи. Интерфейс решил реализовать в виде телеграм бота. Добавил ещё несколько криптовалют. Можно масштабировать и смотреть текущий курс вручную. По заданию, есть возможность отслеживать колебания курса валют от 1% включительно. Время проверки изменения курса снизил до 10 секунд. Можно отключить отправку сообщений."
    text+="\n\nМои контакты - @bubba1983"
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(button_back_to_main_menu2)     
    try:
        await bot.edit_message_text(chat_id=menu_ids[0], message_id=menu_ids[1],reply_markup=keyboard, text=text)
    except:
        print(f"ERROR")
@dp.message_handler(commands=['start','menu'])
async def process_start_command(message: types.Message,state: FSMContext):
    await state.finish()
    await start_main_menu(message)
    try:
        await bot.delete_message(chat_id=message.chat.id,message_id=message.message_id)
    except:
        print(f"ERROR delete_message")
@dp.message_handler(commands=['help','info'])
async def process_help_command(message: types.Message,state: FSMContext):
    await state.finish()
    try:
        await bot.send_message(message.from_user.id,text="/menu вызов главного меню")
    except:
        print(f"ERROR")
    try:
        await bot.delete_message(chat_id=message.chat.id,message_id=message.message_id)
    except:
        print(f"ERROR delete_message")

@dp.callback_query_handler()
async def send_random_value(call: types.CallbackQuery,state: FSMContext):
    await state.finish()
    if await check_profile(call):
        if call.data == "back_menu":
            await start_main_menu(call)
        elif call.data == "test":
            await start_main_menu(call)
        elif call.data == "info":
            await info(call)
        elif "coin_" in call.data:
            await coin_info(call)
        elif call.data == "coins":
            await coins(call)
        elif call.data == "watch":
            await watch(call)
        elif "watch_" in call.data:
            await start_main_menu(call)
            await watch_set(call)
            await watch_start(call)
        elif call.data == "stop":
            await stop(call)
        elif "stop_" in call.data:
            await stop_coin(call)
            await start_main_menu(call)

@dp.callback_query_handler(state=Form.name)
async def send_random_value(call: types.CallbackQuery,state: FSMContext):
    await state.finish()
    if call.data == "back_menu":
        await start_main_menu(call)

async def reset_limits():
    print("TIME")
@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.finish()
    try:
        await bot.delete_message(chat_id=message.chat.id,message_id=message.message_id)
    except:
        print(f"ERROR delete_message") 
def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(TEST_TIME, repeat, coro, loop)
@dp.message_handler(content_types='text')
async def title_h(message: types.Message):
    user_id=message.from_user.id
    msg=f"📨TEST\nID: {message.from_user.id}\nName: {message.from_user.first_name} {message.from_user.last_name} \nUSERNAME: @{message.from_user.username}\nUSER MESSAGE:\n<b>{message.text}</b>"
    msg+=f"\nLINK: <a href='tg://user?id={message.from_user.id}'>LINK</a> "
    for n in admin_id:
        if user_id!=n:
            try:
                await bot.send_message(n, text=msg,parse_mode="HTML")
            except:
                print(f"ERROR")
    if(not message.text.isdigit()):
        await bot.send_message(message.from_user.id, text=f"Данный бот не сможет ответить на данное сообщение\nОно будет отправлено админу\n@bubba1983",parse_mode="HTML")
    try:
        await bot.delete_message(chat_id=message.chat.id,message_id=message.message_id)
    except:
        print(f"ERROR delete_message")  
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.call_later(TEST_TIME, repeat, reset_limits, loop)
    executor.start_polling(dispatcher=dp, timeout=2, relax=0, fast=True,loop=loop)
