from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# Book Schemas
class BookBase(BaseModel):
    title: str
    author: str
    category: str
    isbn: str
    availability_status: Optional[str] = "available"


class BookCreate(BookBase):
    pass


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    isbn: Optional[str] = None
    availability_status: Optional[str] = None


class BookResponse(BookBase):
    book_id: int

    class Config:
        from_attributes = True


# Borrower Schemas
class BorrowerBase(BaseModel):
    borrower_name: str
    email: str
    phone: str


class BorrowerCreate(BorrowerBase):
    pass


class BorrowerUpdate(BaseModel):
    borrower_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class BorrowerResponse(BorrowerBase):
    borrower_id: int

    class Config:
        from_attributes = True


# Transaction Schemas
class BorrowRequest(BaseModel):
    book_id: int
    borrower_id: int


class ReturnRequest(BaseModel):
    transaction_id: int


class TransactionResponse(BaseModel):
    transaction_id: int
    book_id: int
    borrower_id: int
    borrow_date: datetime
    return_date: Optional[datetime] = None
    book: Optional[BookResponse] = None
    borrower: Optional[BorrowerResponse] = None

    class Config:
        from_attributes = True
