import requests
from bs4 import BeautifulSoup
import re
from user_agent import generate_user_agent

from db import insert, clear_all_tables

import socks
import socket
socks.set_default_proxy(socks.SOCKS5, "localhost", 9150)
socket.socket = socks.socksocket

lovikod_link = 'https://lovikod.ru/knigi/promokody-litres'


def link_processing(link):
    name = link[link.find('.ru') + 3:link.find('lfrom') - 1]
    return 'https://www.litres.ru' + name


def add_table_to_database(table):
    '''
    Add promocodes into "promocodes" table
    '''
    row_index = 1
    collections = []
    promocodes = []
    for row in table.find_all('tr')[1:]:
        columns = row.find_all('td')
        date = columns[0].text
        text = link_processing(columns[1].find('a')['href']) if columns[1].get_text() == '[автокод]' else columns[1].get_text().replace('\n', ' ')
        description = columns[2].text
        collection_link = link_processing(columns[2].find('a')['href']) if columns[2].find('a') is not None else '-'
        if re.search(r'\d+%', description) is not None:
            rate = int(re.search(r'\d+%', description)[0][:-1])
        elif re.search(r'бесплатно', description):
            rate = 100
        else:
            rate = 0
        promocodes.append((row_index, date, description, text, rate, collection_link))
        collections.append((row_index, collection_link))
        row_index += 1
    insert('promocodes', promocodes)
    print('Table promocodes is filled')
    return collections


def parse_link_with_collection(index_collection):
    prc_id = index_collection[0]
    collection_link = index_collection[1]
    if collection_link == '-':
        return
    prc_books = []
    test_request = requests.get(collection_link, headers={'User-Agent': generate_user_agent()})
    if collection_link.find('kollekcii-knig') != -1 or collection_link.find('luchshie-knigi'):
        try:
            pages_num = int(BeautifulSoup(test_request.text, 'html.parser').find('div', {'class': 'books_container'})['data-pages'])
        except TypeError:
            pages_num = 1
        for i in range(1, pages_num + 1):
            request = requests.get(collection_link + f'page-{i}', headers={'User-Agent': generate_user_agent()})
            bs = BeautifulSoup(request.text, 'html.parser')

            for book in bs.find_all('div', {'class': 'art-item'}):
                link = 'https://www.litres.ru' + book.find('div', {'class': 'cover-image-wrapper'}).find('a')['href']
                author = book.find('div', {'class': 'art__author'}).text
                title = book.find('div', {'class': 'art__name'}).text
                prc_books.append((prc_id, link))
                insert('books', [(link, author, title)])
    elif collection_link.find('my_account') != -1:
        return

    else: # если в подборке только одна книга, то даётся прямая ссылка на неё
        soup = BeautifulSoup(test_request.text, 'html.parser')
        author = soup.find('a', {'class': 'biblio_book_author__link'}).get_text()
        title = soup.find_all('li', {'class': 'breadcrumbs__item'})[-1].text
        prc_books.append((prc_id, collection_link))
        insert('books', [(collection_link, author, title)])
    insert('prcbooks', prc_books)



def update():
    # delete all rows from 3 tables
    clear_all_tables()
    r = requests.get(lovikod_link)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table')
    index_collections = add_table_to_database(table)
    for index in index_collections[35:]:
        try:
            parse_link_with_collection(index)
            print(f'{index} - success')
        except Exception:
            print(f'{index} - NOT success')


if __name__ == "__main__":
    update()
