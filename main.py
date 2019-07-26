import requests
import json
from flask import Flask, request
import pandas as pd
from random import randint

from parse_litres import search_link_in_database
from token_storage import TOKEN, path
URL = 'https://api.telegram.org/bot' + TOKEN


sdf = pd.read_csv(path + 'sdf_2.csv', index_col=0)
df_with_correct_paths = sdf[sdf['Path'] != '---']

app = Flask(__name__)

def write_json(data, filename='answer.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def send_message(chat_id, text):
    url = URL + '/sendMessage'
    message = {'chat_id': chat_id, 'text': text}
    r = requests.post(url, json=message)
    return r.json()


def make_answer(link):
    if link.find('litres.ru') == -1:
        return u'\U0001F50E' \
               u'\U0000274C' \
               ' Это не похоже на ссылку!\n Найдите книгу на www.litres.ru, скопируйте ссылку и пришлите её боту'

    df = search_link_in_database(sdf, link)
    if (df.shape[0] == 0):
        return u'\U0001F61E' \
               ' К сожалению, этой книги нет в бесплатных подборках\nПосмотрите раздел /sale со скидками на книги'

    answer = u'\U0001F4D6' \
             ' Ура! Книга нашлась в бесплатных подборках:\n'
    for i in range(df.shape[0]):
        date = pd.to_datetime(df.loc[i, 'To'], format='%Y-%m-%d %H:%M:%S') - pd.Timedelta(seconds=1)
        answer += '{}) '.format(i + 1) + df.loc[i, 'Description'] +\
                  '\nПромокод/ссылка: ' + df.loc[i, 'Promocode'] + '\nДействует до: ' + \
                  str(date.day).zfill(2) + '. ' + str(date.month).zfill(2) + '\n\n'
    return answer

def gen_sale():
    answer = (u'\U0001F525')*3 + ' Самые высокие скидки на книги: \n\n'
    for i in range(10):
        date = pd.to_datetime(sdf.loc[i, 'To'], format='%Y-%m-%d %H:%M:%S') - pd.Timedelta(seconds=1)
        answer += '{}) '.format(i+1) + sdf.loc[i, 'Description']+ \
            '\nПромокод/ссылка: ' + sdf.loc[i, 'Promocode'] + '\nДействует до: ' + \
            str(date.day).zfill(2) + '. ' + str(date.month).zfill(2) + '\n\n'
    return answer + u'\U0001F4DA' + ' Мало скидок? Посмотрите раздел /more_sales '

def gen_more_sales():
    answer = u'\U0001F4A3' + ' Ещё больше скидок: \n\n'
    for i in range(10, 30):
        date = pd.to_datetime(sdf.loc[i, 'To'], format='%Y-%m-%d %H:%M:%S') - pd.Timedelta(seconds=1)
        answer += '{}) '.format(i - 9) + sdf.loc[i, 'Description'] + \
                  '\nПромокод/ссылка: ' + sdf.loc[i, 'Promocode'] + '\nДействует до: ' + \
                  str(date.day).zfill(2) + '. ' + str(date.month).zfill(2) + '\n\n'
    return answer

def gen_free_random():
    answer = u'\U000026A1' + ' Бесплатные книги из подборки: \n'
    random_index = randint(0, df_with_correct_paths.shape[0]-1)
    date = pd.to_datetime(df_with_correct_paths.iloc[random_index, 0], format='%Y-%m-%d %H:%M:%S')\
            - pd.Timedelta(seconds=1)

    answer += df_with_correct_paths.iloc[random_index, 2] +\
            '\nПромокод/ссылка: ' + df_with_correct_paths.iloc[random_index, 1] + '\nДействует до: ' +\
            str(date.day).zfill(2) + '. ' + str(date.month).zfill(2) + '\n\n\n'

    file_path = df_with_correct_paths.iloc[random_index, 5]
    df = pd.read_csv(path + file_path, index_col=0)
    books_amount = min(10, df.shape[0])
    if books_amount == 0: # наткнулся на пустой список
        return gen_free_random()
    else:
        for i in range(books_amount):
            answer += '{}) '.format(i+1) + df.loc[i, 'Author'] + ' «' + df.loc[i, 'Title'] + '» '
            answer += ('(Аудио)') if df.loc[i, 'Is_Audio'] else ''
            answer += '\n' + 'https://www.litres.ru' + df.loc[i, 'Link'] + '\n\n'
        return answer + u'\U0001F914' + ' Не нашли ничего интересного? Напишите /free_random ещё раз!'

def start_message():
    answer = '<b>Привет!</b>\n Основная функция бота - поиск интересующей тебя книги среди бесплатных подборок. ' +\
            'Для этого найди книгу на ЛитРес, скопируй ссылку и отправь мне. \n Если её нет в подборках, ' +\
            'могу предложить другие бесплатные книги (/free_random) или скидки, действующие на все книги (/sale)\n\n' +\
            u'\U0001F916'  + ' Если бот не сразу отвечает, подождите немного, пожалуйста, он подумает и обязательно ответит :)' +\
            u'\U0001F468' + u'\U0000200D' + u'\U0001F4BB' + ' создатель: @amsavchenko'
    return answer


@app.route('/' + TOKEN, methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        r = request.get_json()
        chat_id = r['message']['chat']['id']
        message = r['message']['text']
        if '/sale' in message:
            send_message(chat_id, gen_sale())
        elif '/more_sales' in message:
            send_message(chat_id, gen_more_sales())
        elif '/free_random' in message:
            send_message(chat_id, gen_free_random())
        elif '/start' in message:
            send_message(chat_id, start_message())
        else:
            send_message(chat_id, make_answer(message))
        return 'success'
    return '<h1> Hello bot </h1>'

@app.route('/')
def test():
    return '<h1> TEEEST!!! </h1>'


if __name__ == "__main__":
    app.run()
    

