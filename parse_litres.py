import requests
from bs4 import BeautifulSoup
import pandas as pd
from user_agent import generate_user_agent
import os
import glob

# для того, чтобы все запросы отправлялись через ТОР
# (надо держать тор открытым) 
# пакет PySocks 
import socks 
import socket 
socks.set_default_proxy(socks.SOCKS5, "localhost", 9150)
socket.socket = socks.socksocket

from token_storage import path # путь до папки storage с csv-файлами

def extract_month(string):
    # вытягивает из строки вида "июль 2019" месяц и преобразует в дату
    # вида 01.08.2019 - т.е. ДО какого дня будет работать промокод
    month = string[:string.rfind(' ')]
    year = string[string.find(' ') + 1:]
    if (month == 'январь'):
        month = '01.02.'
    elif (month == 'февраль'):
        month = '01.03.'
    elif (month == 'март'):
        month = '01.04.'
    elif (month == 'апрель'):
        month = '01.05.'
    elif (month == 'май'):
        month = '01.06.'
    elif (month == 'июнь'):
        month = '01.07.'
    elif (month == 'июль'):
        month = '01.08.'
    elif (month == 'август'):
        month = '01.09.'
    elif (month == 'сентябрь'):
        month = '01.10.'
    elif (month == 'октябрь'):
        month = '01.11.'
    elif (month == 'ноябрь'):
        month = '01.12.'
    elif (month == 'декабрь'):
        month = '01.01.'
    return month + year


def link_processing(link):
    name = link[link.find('.ru') + 3:link.find('lfrom') - 1]
    return 'https://www.litres.ru' + name


def fill_df_from_table(df, table):
    row_marker = 1
    for row in table.find_all('tr')[1:]:
        columns = row.find_all('td')

        date = columns[0].get_text()
        if date[:2] == 'до':
            date = date[date.find(' ')+1:]
        else:
            date = extract_month(date)

        df.loc[row_marker, 'To'] = pd.to_datetime(date, format='%d.%m.%Y')
        df.loc[row_marker, 'Promocode'] = link_processing(columns[1].find('a')['href']) if columns[1].get_text() == '[автокод]' else columns[1].get_text().replace('\n', ' ')
        df.loc[row_marker, 'Description'] = columns[2].get_text()
        df.loc[row_marker, 'Collection'] = ''

        if ((df.loc[row_marker, 'Description'].find('Скидка') == -1) or \
            ((df.loc[row_marker, 'Description'].find('Скидка') != -1) and (df.loc[row_marker, 'Description'].find('+') != -1))):
            df.loc[row_marker, 'Collection'] = link_processing(columns[2].find_all('a')[-1]['href'])

        df.loc[row_marker, '%'] = 0

        if (df.loc[row_marker, 'Description'].find('%') != -1):
            df.loc[row_marker, '%'] = int(df.loc[row_marker, 'Description'][df.loc[row_marker, 'Description'].find('%')-2:\
                                                                         df.loc[row_marker, 'Description'].find('%')])

        row_marker += 1
    return df

def parse_link_with_collection(link):
    books_df = pd.DataFrame(columns = ['Link', 'Author', 'Title', 'Is_Audio'])
    test_request = requests.get(link, headers={'User-Agent': generate_user_agent()})
    if (link.find('kollekcii-knig') != -1):
        index = 0
        try:
            pages_num = int(BeautifulSoup(test_request.text, 'html.parser').find('div', {'class': 'left_column books_container'})['data-pages'])
        except TypeError:
            return books_df
        else:
            for i in range (1, pages_num + 1):
                #sleep(np.random.random())
                request = requests.get((link + 'page-%d') % i, headers={'User-Agent': generate_user_agent()})
                bs = BeautifulSoup(request.text, 'html.parser')
                for book in bs.find_all('div', {'class': 'art-item'}):
                    try:
                        books_df.loc[index, 'Link'] = book.find('div', {'class': 'art-item__name'}).find('a')['href']
                        books_df.loc[index, 'Author'] = book.find('div', {'class': 'art-item__author'}).get_text()
                        books_df.loc[index, 'Title'] = book.find('div', {'class': 'art-item__name'}).get_text()
                        books_df.loc[index, 'Is_Audio'] = book.find('div', {'class': 'art-item__name_audio'}) is not None
                    except TypeError:
                        books_df.loc[index, 'Link'] = '-'
                        books_df.loc[index, 'Author'] = '-'
                        books_df.loc[index, 'Title'] = '-'
                        books_df.loc[index, 'Is_Audio'] = '-'
                    finally:
                        index += 1
    else: # если в подборке только одна книга, то даётся прямая ссылка на неё
        try:
            soup = BeautifulSoup(test_request.text, 'html.parser')
            books_df.loc[0, 'Link'] = link[link.find('.ru')+3:]
            books_df.loc[0, 'Author'] = soup.find('a', {'class': 'biblio_book_author__link'}).get_text()
            full_title = soup.find('h1', {'itemprop':'name'}).get_text()
            books_df.loc[0, 'Title'] = full_title[:full_title.find('\xa0')]
            books_df.loc[0, 'Is_Audio'] = full_title[full_title.find('\xa0')+1:] == 'Аудио'
        except TypeError:
            books_df.loc[0, 'Link'] = books_df.loc[0, 'Author'] = books_df.loc[0, 'Title'] = books_df.loc[0, 'Is_Audio'] = '-'
        except AttributeError:
            books_df.loc[0, 'Link'] = books_df.loc[0, 'Author'] = books_df.loc[0, 'Title'] = books_df.loc[0, 'Is_Audio'] = '-'
    return books_df


def save_csv_with_collection_and_get_path(link):
    if (link == ''):
        file_name = '---'
    else:
        books_df = parse_link_with_collection(link)
        file_name = link[link.find('.ru')+4:-1].replace('/', '_') + '.csv'
        books_df.to_csv(path + file_name)
    return file_name


def check_csv_for_link(filename, link):
    try:
        df = pd.read_csv(path + filename)
    except FileNotFoundError:
        return False

    link = link[link.find('.ru') + 3:]
    for link_from_csv in df['Link']:
        if (link_from_csv == link):
            return True
    return False


def search_link_in_database(df, link):
    answer = pd.DataFrame(columns=['To', 'Promocode', 'Description'])
    answer_index = 0
    for i in range(df.shape[0]):
        filename = df.loc[i, 'Path']
        if (check_csv_for_link(filename, link)):
            answer.loc[answer_index] = df.loc[i, ['To', 'Promocode', 'Description']]
            answer_index += 1
    return answer


def update():
    r = requests.get('https://lovikod.ru/knigi/promokody-litres')
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find_all('table')[0]

    df = pd.DataFrame(columns=['To', 'Promocode', 'Description', 'Collection', '%'], \
                      index=[i for i in range(1, len(table.find_all('tr')))])

    df = fill_df_from_table(df, table)

    sdf = df.sort_values('%', ascending=False)
    sdf.index = [i for i in range(len(sdf.index))]

    sdf['Path'] = sdf['Collection'].apply(save_csv_with_collection_and_get_path)

    sdf.to_csv(path + 'sdf_2.csv')


def clean_storage_folder(path):
    files = glob.glob(path + '*')
    for f in files:
        os.remove(f)


if __name__ == "__main__":
    clean_storage_folder(path)
    update()

