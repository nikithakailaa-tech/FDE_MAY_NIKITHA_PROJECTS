-- Library Management System - Database Schema
-- SQLite compatible

CREATE TABLE IF NOT EXISTS books (
    book_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title             TEXT    NOT NULL,
    author            TEXT    NOT NULL,
    category          TEXT    NOT NULL,
    isbn              TEXT    NOT NULL UNIQUE,
    availability_status TEXT  NOT NULL DEFAULT 'available'
);

CREATE TABLE IF NOT EXISTS borrowers (
    borrower_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    borrower_name TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    phone         TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INTEGER  PRIMARY KEY AUTOINCREMENT,
    book_id        INTEGER  NOT NULL REFERENCES books(book_id),
    borrower_id    INTEGER  NOT NULL REFERENCES borrowers(borrower_id),
    borrow_date    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    return_date    DATETIME
);

-- Sample seed data
INSERT INTO books (title, author, category, isbn, availability_status) VALUES
  ('Clean Code', 'Robert C. Martin', 'Technology', '9780132350884', 'available'),
  ('The Pragmatic Programmer', 'David Thomas', 'Technology', '9780201616224', 'available'),
  ('To Kill a Mockingbird', 'Harper Lee', 'Fiction', '9780061935466', 'available'),
  ('1984', 'George Orwell', 'Fiction', '9780451524935', 'available'),
  ('Sapiens', 'Yuval Noah Harari', 'Non-Fiction', '9780062316097', 'available');

INSERT INTO borrowers (borrower_name, email, phone) VALUES
  ('Alice Johnson', 'alice@example.com', '9876543210'),
  ('Bob Smith', 'bob@example.com', '9123456780');
