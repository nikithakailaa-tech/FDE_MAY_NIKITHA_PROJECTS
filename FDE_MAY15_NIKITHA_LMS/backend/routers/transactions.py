from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import crud
import schemas
from database import get_db

router = APIRouter(tags=["Transactions & Search"])


@router.post("/borrow", response_model=schemas.TransactionResponse, status_code=201)
def borrow_book(borrow_req: schemas.BorrowRequest, db: Session = Depends(get_db)):
    transaction, error = crud.borrow_book(db, borrow_req)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return transaction


@router.post("/return", response_model=schemas.TransactionResponse)
def return_book(return_req: schemas.ReturnRequest, db: Session = Depends(get_db)):
    transaction, error = crud.return_book(db, return_req)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return transaction


@router.get("/transactions", response_model=List[schemas.TransactionResponse])
def get_transactions(db: Session = Depends(get_db)):
    return crud.get_transactions(db)


@router.get("/search", response_model=List[schemas.BookResponse])
def search_books(
    q: Optional[str] = None,
    category: Optional[str] = None,
    author: Optional[str] = None,
    db: Session = Depends(get_db),
):
    return crud.search_books(db, query=q, category=category, author=author)


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    return crud.get_dashboard_stats(db)
