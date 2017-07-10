CREATE TABLE articles(
   id CHAR(14) PRIMARY KEY     NOT NULL,
   description           TEXT    NOT NULL,
   tags            TEXT     NOT NULL,
   article           TEXT   NOT NULL,
   author        CHAR(20)     NOT NULL,
   title        CHAR(50)     NOT NULL,
   feature      INT      NOT NULL,
   created_at         INT     NOT NULL,
   updated_at         INT     NOT NULL,
   show        INT      NOT NULL
);