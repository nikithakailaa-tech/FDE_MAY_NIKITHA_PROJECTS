from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import crud
import schemas
from database import get_db

router = APIRouter(prefix="/borrowers", tags=["Borrowers"])


@router.get("/", response_model=List[schemas.BorrowerResponse])
def get_borrowers(db: Session = Depends(get_db)):
    return crud.get_borrowers(db)


@router.post("/", response_model=schemas.BorrowerResponse, status_code=201)
def create_borrower(borrower: schemas.BorrowerCreate, db: Session = Depends(get_db)):
    return crud.create_borrower(db, borrower)


@router.put("/{borrower_id}", response_model=schemas.BorrowerResponse)
def update_borrower(borrower_id: int, borrower: schemas.BorrowerUpdate, db: Session = Depends(get_db)):
    updated = crud.update_borrower(db, borrower_id, borrower)
    if not updated:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return updated


@router.delete("/{borrower_id}", response_model=schemas.BorrowerResponse)
def delete_borrower(borrower_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_borrower(db, borrower_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Borrower not found")
    return deleted
