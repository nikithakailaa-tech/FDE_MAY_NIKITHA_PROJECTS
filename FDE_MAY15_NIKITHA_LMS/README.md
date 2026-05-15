# Library Management System (LMS)

## Project Overview

A full-stack web application for managing books, borrowers, and borrowing transactions in a library. Built as Phase 1 of the capstone project.

## Features Implemented

- **Book Management** — Add, view, update, delete books; track availability
- **Borrower Management** — Add, view, update, delete borrowers
- **Borrow / Return Workflow** — Borrow available books, return them, auto-update status
- **Search** — Keyword search across title, author, category, ISBN; filter by category or author
- **Dashboard** — Live stats (total books, available, borrowed, borrowers) + recent transactions

## Technology Stack

| Layer       | Technology              |
|-------------|-------------------------|
| Frontend    | React 18 + Vite         |
| Backend     | Python FastAPI          |
| Database    | SQLite (via SQLAlchemy) |
| HTTP Client | Axios                   |
| Routing     | React Router v6         |

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will open at `http://localhost:3000`.

### Database Setup

SQLite database (`library.db`) is auto-created on first backend run.  
To seed sample data manually:

```bash
sqlite3 backend/library.db < database/schema.sql
```

## API Endpoints

### Books
| Method | Endpoint       | Description        |
|--------|----------------|--------------------|
| GET    | /books/        | List all books     |
| GET    | /books/{id}    | Get book by ID     |
| POST   | /books/        | Add new book       |
| PUT    | /books/{id}    | Update book        |
| DELETE | /books/{id}    | Delete book        |

### Borrowers
| Method | Endpoint            | Description           |
|--------|---------------------|-----------------------|
| GET    | /borrowers/         | List all borrowers    |
| POST   | /borrowers/         | Add borrower          |
| PUT    | /borrowers/{id}     | Update borrower       |
| DELETE | /borrowers/{id}     | Delete borrower       |

### Transactions & Search
| Method | Endpoint        | Description                        |
|--------|-----------------|------------------------------------|
| POST   | /borrow         | Borrow a book                      |
| POST   | /return         | Return a book                      |
| GET    | /transactions   | List all transactions              |
| GET    | /search         | Search books (params: q, category, author) |
| GET    | /dashboard      | Dashboard statistics               |

## Project Structure

```
lms/
├── backend/
│   ├── main.py         # FastAPI app entry point
│   ├── database.py     # SQLAlchemy engine & session
│   ├── models.py       # ORM models
│   ├── schemas.py      # Pydantic request/response schemas
│   ├── crud.py         # Database operations
│   ├── routers/
│   │   ├── books.py
│   │   ├── borrowers.py
│   │   └── transactions.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/Navbar.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Books.jsx
│   │   │   ├── Borrowers.jsx
│   │   │   ├── Transactions.jsx
│   │   │   └── Search.jsx
│   │   ├── services/
│   │   │   ├── bookService.js
│   │   │   ├── borrowerService.js
│   │   │   └── transactionService.js
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── index.css
│   ├── index.html
│   └── package.json
├── database/
│   └── schema.sql
├── docs/
├── screenshots/
├── .gitignore
└── README.md
```

## Evaluation Criteria Coverage

| Criteria               | Status |
|------------------------|--------|
| Frontend Development   | ✅ React, hooks, components, Axios, form validation, responsive |
| Backend API Development| ✅ FastAPI, Pydantic, REST standards, CORS, exception handling |
| Database Integration   | ✅ SQLite via SQLAlchemy ORM, proper schema with FK relationships |
| CRUD Functionality     | ✅ Full CRUD for Books and Borrowers |
| Search/Filter Features | ✅ Keyword + category + author filters |
| Code Quality & Structure | ✅ Layered architecture, modular routers, service-based frontend |
| Documentation          | ✅ README, API table, setup guide |
