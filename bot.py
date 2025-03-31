import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
import requests

API_TOKEN = "7805102550:AAE6h4NplvoXaWhJoVB85yKVWymuHj-WMyM"
API_KEY = 'cc7279828827aa430d91d763fbc16083'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

ADMIN = {5932796462}
block_users = set()


class Form(StatesGroup):
    name = State()
    age = State()


menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📖 Команды"), KeyboardButton(text="📊 Статистика")],
        [KeyboardButton(text="📝 Помощь"), KeyboardButton(text="❌ Выйти")]
    ],
    resize_keyboard=True
)


# Админ-панель
def get_admin_panel():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔒 Забанить", callback_data="ban"),
             InlineKeyboardButton(text="✅ Разбанить", callback_data="unban")]
        ]
    )


# ✅ Обработчик команды /start
@router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Привет! Это бот, который может выполнять команды. Используйте меню ниже.",
                         reply_markup=menu_keyboard)


# ✅ Обработчик команды /reg (FSM)
@router.message(Command("reg"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.set_state(Form.name)
    await message.answer("Как тебя зовут?")


@router.message(StateFilter(Form.name))
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("Сколько тебе лет?")


@router.message(StateFilter(Form.age))
async def process_age(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name")
    age = message.text
    await message.answer(f"✅ Вы зарегистрировались!\nИмя: {name}\nВозраст: {age}")
    await state.clear()


# ✅ Админ-панель
@router.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id in ADMIN:
        await message.answer("🛠 Админ-панель", reply_markup=get_admin_panel())
    else:
        await message.answer("🚫 У вас нет прав на админство.")


# ✅ Блокировка/разблокировка пользователей
@router.callback_query(F.data.in_(["ban", "unban"]))
async def handle_admin_actions(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN:
        await callback.answer("🚫 У вас нет прав на это действие!", show_alert=True)
        return

    if callback.message.reply_to_message:
        user_id = callback.message.reply_to_message.from_user.id
        if callback.data == "ban":
            if user_id in ADMIN:
                await callback.message.answer("⚠ Вы не можете забанить админа!")
                return
            block_users.add(user_id)
            await callback.message.answer(f"🔒 Пользователь {user_id} заблокирован.")

        elif callback.data == "unban":
            block_users.discard(user_id)
            await callback.message.answer(f"✅ Пользователь {user_id} разблокирован.")
    else:
        await callback.message.answer("⚠ Ответьте на сообщение пользователя для блокировки/разблокировки!")

    await callback.answer()


# ✅ Проверка забаненных пользователей
@router.message()
async def check_blocked_users(message: types.Message):
    if message.from_user.id in block_users:
        await message.answer("🚫 Вы заблокированы и не можете писать сообщения.")
        return

    # Обработка команд из меню
    if message.text == "📖 Команды":
        await message.answer("Доступные команды: /start, /help, /stats, /reg, /admin")
    elif message.text == "📊 Статистика":
        await message.answer("📊 Статистика недоступна.")
    elif message.text == "📝 Помощь":
        await message.answer("Отправь команду /start, чтобы увидеть меню.")
    elif message.text == "❌ Выйти":
        await message.answer("Меню скрыто. Напишите /start, чтобы вернуть его.",
                             reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("Выберите команду из меню.", reply_markup=menu_keyboard)


# Функция для получения погоды
def get_weather(city: str):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru'
    response = requests.get(url)
    data = response.json()

    if data.get('cod') != 200:
        return None

    city_name = data['name']
    country = data['sys']['country']
    temperature = data['main']['temp']
    weather = data['weather'][0]['description']
    humidity = data['main']['humidity']
    wind_speed = data['wind']['speed']

    return f"Погода в {city_name}, {country}:\nТемпература: {temperature}°C\n{weather.capitalize()}\nВлажность: {humidity}%\nСкорость ветра: {wind_speed} м/с"


# Команда /start
@router.message(Command("weather"))
async def cmd_weather(message: types.Message):
    await message.answer("Привет! Я бот, который может показать погоду в любом городе. Введите название города.")


# Команда для получения погоды
@router.message()
async def get_weather_command(message: types.Message):
    city = message.text.strip()

    weather_info = get_weather(city)
    if weather_info:
        await message.answer(weather_info, parse_mode='Markdown')  # Используем строку 'Markdown'
    else:
        await message.answer("Город не найден. Проверьте название и попробуйте снова.")


# ✅ Функция запуска бота
async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)

    # Установка команд бота
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Запустить бота"),
        types.BotCommand(command="reg", description="Регистрация"),
        types.BotCommand(command="admin", description="Админ-панель"),
        types.BotCommand(command="help", description="Помощь"),
        types.BotCommand(command="stats", description="Статистика"),
        types.BotCommand(command="weather", description="Погода")
    ])

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
