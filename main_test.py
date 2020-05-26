import logging
from aiogram import Bot, Dispatcher, executor, types

from token_storage import TOKEN
from db import select_sales, select_random_collection, select_book_by_link, select_book_by_title_or_author


logging.basicConfig(level=logging.INFO)
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
async def sales(message: types.Message):
    rows = select_sales()
    answer = (u'\U0001F525')*3 + ' Самые высокие скидки на книги:\n\n'
    for index, row in enumerate(rows, 1):
        answer += f'{index}) {row[1]}\nПромокод/ссылка: {row[2]}\nДействует до: {row[0]}\n\n'
    answer += u'\U0001F4DA' + ' Мало скидок? Посмотрите раздел /more_sales '
    await message.answer(answer)


@dp.message_handler(commands=['more_sales'])
async def more_sales(message: types.Message):
    rows = select_sales(30)[10:]
    answer = u'\U0001F4A3' + ' Ещё больше скидок: \n\n'
    for index, row in enumerate(rows, 1):
        answer += f'{index}) {row[1]}\nПромокод/ссылка: {row[2]}\nДействует до: {row[0]}\n\n'
    answer += 'Ищешь что-то конкретное? Отправь мне ссылку на книгу / или ...'
    await message.answer(answer)


@dp.message_handler(commands=['free_random'])
async def free_random(message: types.Message):
    description_text, rows = select_random_collection()
    answer = u'\U000026A1' + f' Бесплатные книги из подборки: {description_text[0]}\nПромокод/ссылка: {description_text[1]}\n\n'
    for index, row in enumerate(rows, 1):
        answer += f'{index}) "{row[2]}"\nАвтор: {row[1]}\nСсылка: {row[0]}\n\n'
    answer += u'\U0001F914' + ' Не нашли ничего интересного? Напишите /free_random ещё раз!'
    await message.answer(answer)


@dp.message_handler(lambda message : 'litres.ru' in message.text)
async def search_link(message: types.Message):
    rows = select_book_by_link(message.text)
    if not rows:
        answer = u'\U0001F61E' + ' К сожалению, этой книги нет в бесплатных подборках\nПосмотри раздел /sale со скидками на книги'
    else:
        answer = u'\U0001F4D6' + ' Ура! Книга нашлась в бесплатных подборках:\n'
        for index, row in enumerate(rows, 1):
            answer += f'{index}) {row[0]}\nПромокод/ссылка: {row[1]}\n\n'
    await message.answer(answer)


@dp.message_handler()
async def search_title_or_author(message: types.Message):
    search_result = select_book_by_title_or_author(message.text)
    if not search_result:
        answer = u'\U0001F61E' + ' К сожалению, такой книги нет в бесплатных подборках\nПосмотри раздел /sale со скидками на книги'
    else:
        answer = u'\U0001F4D6' + ' Вот, что я нашёл:\n'
        for index, book in enumerate(search_result, 1):
            answer += f'{index}) "{book[1]}"\nАвтор: {book[2]}\nСсылка: {book[0]}\n\n'
            for collection in book[3]:
                answer += f'Подборка: {collection[0]}\nПромокод/ссылка: {collection[1]}\n'
            answer += '\n\n'
    await message.answer(answer)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
