create table promocodes(
    prc_id integer primary key,
    prc_date text,
    prc_description text,
    prc_text text,
    prc_rate integer,
    collection_link text
);

create table books(
    book_link text primary key,
    book_author text,
    book_title text
);

create table prcbooks(
    prc_id integer,
    book_link integer,
    primary key (prc_id, book_link),
    foreign key prc_id references promocodes(prc_id),
    foreign key book_link references books(book_link)
);