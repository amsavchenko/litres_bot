import logging

from aiogram import Bot, Dispatcher, executor, types

from token_storage import TOKEN
from db import select_sales

logging.basicConfig(level=logging.INFO)

# initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    answer = u'\U0001F4D6' + ' Привет!\n\nОсновная функция бота — поиск интересующей тебя книги среди бесплатных подборок. ' + \
             'Для этого найди книгу на ЛитРес, скопируй ссылку и отправь мне. \n\nЕсли её нет в подборках, ' + \
             'могу предложить другие бесплатные книги (/free_random) или скидки, действующие на все книги (/sale)\n\n' + \
             u'\U0001F916' + ' Иногда бот долго думает, но всё равно обязательно ответит\n' + \
             u'\U0001F468' + u'\U0000200D' + u'\U0001F4BB' + 'создатель: @amsavchenko'
    await message.answer(answer)


@dp.message_handler(commands=['sale'])
async def sale(message: types.Message):
    rows = select_sales()
    answer = (u'\U0001F525')*3 + ' Самые высокие скидки на книги:\n\n'
    for index, row in enumerate(rows, 1):
        answer += f'{index}) {row[1]}\nПромокод/ссылка: {row[2]}\nДействует до: {row[0]}\n\n'
    answer += u'\U0001F4DA' + ' Мало скидок? Посмотрите раздел /more_sales '
    await message.answer(answer)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)