from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime
from typing import Optional
import models
import schemas


# ── Books ─────────────────────────────────────────────────────────────────────

def get_books(db: Session):
    return db.query(models.Book).all()


def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.book_id == book_id).first()


def create_book(db: Session, book: schemas.BookCreate):
    db_book = models.Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book


def update_book(db: Session, book_id: int, book: schemas.BookUpdate):
    db_book = get_book(db, book_id)
    if not db_book:
        return None
    update_data = book.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book


def delete_book(db: Session, book_id: int):
    db_book = get_book(db, book_id)
    if not db_book:
        return None
    db.delete(db_book)
    db.commit()
    return db_book


def search_books(db: Session, query: Optional[str] = None, category: Optional[str] = None, author: Optional[str] = None):
    q = db.query(models.Book)
    if query:
        q = q.filter(
            or_(
                models.Book.title.ilike(f"%{query}%"),
                models.Book.author.ilike(f"%{query}%"),
                models.Book.category.ilike(f"%{query}%"),
                models.Book.isbn.ilike(f"%{query}%"),
            )
        )
    if category:
        q = q.filter(models.Book.category.ilike(f"%{category}%"))
    if author:
        q = q.filter(models.Book.author.ilike(f"%{author}%"))
    return q.all()


# ── Borrowers ─────────────────────────────────────────────────────────────────

def get_borrowers(db: Session):
    return db.query(models.Borrower).all()


def get_borrower(db: Session, borrower_id: int):
    return db.query(models.Borrower).filter(models.Borrower.borrower_id == borrower_id).first()


def create_borrower(db: Session, borrower: schemas.BorrowerCreate):
    db_borrower = models.Borrower(**borrower.model_dump())
    db.add(db_borrower)
    db.commit()
    db.refresh(db_borrower)
    return db_borrower


def update_borrower(db: Session, borrower_id: int, borrower: schemas.BorrowerUpdate):
    db_borrower = get_borrower(db, borrower_id)
    if not db_borrower:
        return None
    update_data = borrower.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_borrower, key, value)
    db.commit()
    db.refresh(db_borrower)
    return db_borrower


def delete_borrower(db: Session, borrower_id: int):
    db_borrower = get_borrower(db, borrower_id)
    if not db_borrower:
        return None
    db.delete(db_borrower)
    db.commit()
    return db_borrower


# ── Transactions ──────────────────────────────────────────────────────────────

def get_transactions(db: Session):
    return db.query(models.Transaction).all()


def borrow_book(db: Session, borrow_req: schemas.BorrowRequest):
    book = get_book(db, borrow_req.book_id)
    if not book or book.availability_status != "available":
        return None, "Book is not available"
    borrower = get_borrower(db, borrow_req.borrower_id)
    if not borrower:
        return None, "Borrower not found"
    transaction = models.Transaction(
        book_id=borrow_req.book_id,
        borrower_id=borrow_req.borrower_id,
        borrow_date=datetime.utcnow(),
    )
    book.availability_status = "borrowed"
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction, None


def return_book(db: Session, return_req: schemas.ReturnRequest):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.transaction_id == return_req.transaction_id
    ).first()
    if not transaction:
        return None, "Transaction not found"
    if transaction.return_date:
        return None, "Book already returned"
    transaction.return_date = datetime.utcnow()
    book = get_book(db, transaction.book_id)
    if book:
        book.availability_status = "available"
    db.commit()
    db.refresh(transaction)
    return transaction, None


# ── Dashboard Stats ───────────────────────────────────────────────────────────

def get_dashboard_stats(db: Session):
    total_books = db.query(models.Book).count()
    available_books = db.query(models.Book).filter(models.Book.availability_status == "available").count()
    borrowed_books = db.query(models.Book).filter(models.Book.availability_status == "borrowed").count()
    total_borrowers = db.query(models.Borrower).count()
    recent_transactions = (
        db.query(models.Transaction)
        .order_by(models.Transaction.borrow_date.desc())
        .limit(5)
        .all()
    )
    return {
        "total_books": total_books,
        "available_books": available_books,
        "borrowed_books": borrowed_books,
        "total_borrowers": total_borrowers,
        "recent_transactions": recent_transactions,
    }
