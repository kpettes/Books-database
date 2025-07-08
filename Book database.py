from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLAlchemy setup
DATABASE_URL = "sqlite:///./books.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Book model
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    book_name = Column(String, nullable=False)
    author = Column(String, nullable=False)
    publisher = Column(String, nullable=False)

# Pydantic schemas
class BookCreate(BaseModel):
    book_name: str
    author: str
    publisher: str

class BookOut(BookCreate):
    id: int

    class Config:
        orm_mode = True

# Create DB tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes
@app.post("/books", response_model=BookOut)
def create_book(book: BookCreate):
    db = next(get_db())
    db_book = Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/books", response_model=List[BookOut])
def get_books():
    db = next(get_db())
    return db.query(Book).all()

@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int):
    db = next(get_db())
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.put("/books/{book_id}", response_model=BookOut)
def update_book(book_id: int, updated_book: BookCreate):
    db = next(get_db())
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in updated_book.dict().items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book

@app.delete("/books/{book_id}")
def delete_book(book_id: int):
    db = next(get_db())
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(book)
    db.commit()
    return {"detail": "Book deleted successfully"}
