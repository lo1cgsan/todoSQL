DROP TABLE IF EXISTS users;  -- usunięcie tabeli
CREATE TABLE users (
    id integer primary key autoincrement,
    email text not null
);

DROP TABLE IF EXISTS zadania;  -- usunięcie tabeli
CREATE TABLE zadania (
    id integer primary key autoincrement,
    zadanie text not null,
    zrobione boolean not null default 0,
    data_pub datetime not null,
    id_user integer,
    FOREIGN KEY (id_user) REFERENCES users(id)
);
