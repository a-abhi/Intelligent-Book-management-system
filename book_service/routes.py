from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from models import Book
from schemas import BookCreate, BookResponse
from db import get_db
from utils.auth import verify_auth
from utils.logging import log_action, logger
from utils.book import generate_book_summary
import logging

class BookServiceRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1", tags=["books"])
        self.security = HTTPBasic()
        self._setup_routes()
    
    def _setup_routes(self):
        @self.router.post("/books", response_model=BookResponse)
        async def create_book(
            book: BookCreate,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth),
            credentials: HTTPBasicCredentials = Depends(self.security)
        ):
            try:
                logger.info(f"Attempting to create new book: {book.dict()}")
                
                # Create book first
                db_book = Book(**book.dict())
                db.add(db_book)
                await db.commit()
                await db.refresh(db_book)
                
                # Generate summary if content is provided
                if book.summary:
                    try:
                        generated_summary = await generate_book_summary(
                            book_id=db_book.id,
                            content=book.summary,
                            auth=(credentials.username, credentials.password)
                        )
                        db_book.summary = generated_summary
                        await db.commit()
                        await db.refresh(db_book)
                    except Exception as e:
                        logger.warning(f"Failed to generate summary: {str(e)}")
                        # Continue without summary - don't fail the book creation
                
                logger.info(f"Successfully created book with ID: {db_book.id}")
                await log_action(
                    db=db,
                    user_id=user_id,
                    action="create_book",
                    status="success",
                    details=f"Created book: {db_book.title}"
                )
                return db_book
                
            except IntegrityError as e:
                await db.rollback()
                error_msg = f"Database integrity error while creating book: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action="create_book",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=400,
                    detail="A book with this information already exists"
                )
            except Exception as e:
                await db.rollback()
                error_msg = f"Error creating book: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action="create_book",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error creating book: {str(e)}"
                )

        @self.router.get("/books", response_model=List[BookResponse])
        async def get_books(
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth),
            genre: Optional[str] = Query(None, description="Filter books by genre")
        ):
            try:
                logger.info(f"Attempting to fetch books with genre filter: {genre}")
                
                # Build query based on filters
                stmt = select(Book)
                if genre:
                    stmt = stmt.where(Book.genre == genre)
                
                result = await db.execute(stmt)
                books = result.scalars().all()
                
                logger.info(f"Successfully fetched {len(books)} books")
                await log_action(
                    db=db,
                    user_id=user_id,
                    action="get_books",
                    status="success",
                    details=f"Retrieved {len(books)} books" + (f" with genre {genre}" if genre else "")
                )
                return books
                
            except Exception as e:
                error_msg = f"Error fetching books: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action="get_books",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error fetching books: {str(e)}"
                )

        @self.router.get("/books/{book_id}", response_model=BookResponse)
        async def get_book(
            book_id: int,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth)
        ):
            try:
                logger.info(f"Attempting to fetch book with ID: {book_id}")
                
                stmt = select(Book).where(Book.id == book_id)
                result = await db.execute(stmt)
                book = result.scalar_one_or_none()
                
                if not book:
                    error_msg = f"Book not found with ID: {book_id}"
                    logger.warning(error_msg)
                    await log_action(
                        db=db,
                        user_id=user_id,
                        action=f"get_book_{book_id}",
                        status="failure",
                        details=error_msg
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"Book with ID {book_id} not found"
                    )
                    
                logger.info(f"Successfully found book: {book.title}")
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"get_book_{book_id}",
                    status="success",
                    details=f"Retrieved book: {book.title}"
                )
                return book
                
            except HTTPException:
                raise
            except Exception as e:
                error_msg = f"Error fetching book {book_id}: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"get_book_{book_id}",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error fetching book: {str(e)}"
                )

        @self.router.put("/books/{book_id}", response_model=BookResponse)
        async def update_book(
            book_id: int,
            book: BookCreate,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth),
            credentials: HTTPBasicCredentials = Depends(self.security)
        ):
            try:
                logger.info(f"Attempting to update book with ID: {book_id}")
                logger.info(f"Update data: {book.dict()}")
                
                stmt = select(Book).where(Book.id == book_id)
                result = await db.execute(stmt)
                db_book = result.scalar_one_or_none()
                
                if not db_book:
                    error_msg = f"Book not found with ID: {book_id}"
                    logger.warning(error_msg)
                    await log_action(
                        db=db,
                        user_id=user_id,
                        action=f"update_book_{book_id}",
                        status="failure",
                        details=error_msg
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"Book with ID {book_id} not found"
                    )
                
                # Update book fields
                for key, value in book.dict().items():
                    setattr(db_book, key, value)
                
                # Generate new summary if content is provided
                if book.summary:
                    try:
                        generated_summary = await generate_book_summary(
                            book_id=db_book.id,
                            content=book.summary,
                            auth=(credentials.username, credentials.password)
                        )
                        db_book.summary = generated_summary
                    except Exception as e:
                        logger.warning(f"Failed to generate summary: {str(e)}")
                        # Continue without summary update
                
                await db.commit()
                await db.refresh(db_book)
                
                logger.info(f"Successfully updated book: {db_book.title}")
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"update_book_{book_id}",
                    status="success",
                    details=f"Updated book: {db_book.title}"
                )
                return db_book
                
            except HTTPException:
                raise
            except Exception as e:
                await db.rollback()
                error_msg = f"Error updating book {book_id}: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"update_book_{book_id}",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error updating book: {str(e)}"
                )

        @self.router.delete("/books/{book_id}")
        async def delete_book(
            book_id: int,
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth)
        ):
            try:
                logger.info(f"Attempting to delete book with ID: {book_id}")
                
                stmt = select(Book).where(Book.id == book_id)
                result = await db.execute(stmt)
                book = result.scalar_one_or_none()
                
                if not book:
                    error_msg = f"Book not found with ID: {book_id}"
                    logger.warning(error_msg)
                    await log_action(
                        db=db,
                        user_id=user_id,
                        action=f"delete_book_{book_id}",
                        status="failure",
                        details=error_msg
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"Book with ID {book_id} not found"
                    )
                
                await db.delete(book)
                await db.commit()
                
                logger.info(f"Successfully deleted book: {book.title}")
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"delete_book_{book_id}",
                    status="success",
                    details=f"Deleted book: {book.title}"
                )
                return {"message": f"Book {book_id} deleted successfully"}
                
            except HTTPException:
                raise
            except Exception as e:
                await db.rollback()
                error_msg = f"Error deleting book {book_id}: {str(e)}"
                logger.error(error_msg)
                await log_action(
                    db=db,
                    user_id=user_id,
                    action=f"delete_book_{book_id}",
                    status="failure",
                    details=error_msg
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Error deleting book: {str(e)}"
                )

        @self.router.get("/health")
        async def health_check():
            try:
                logger.info("Health check requested")
                return {"status": "healthy"}
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Service is unhealthy"
                )

# Create router instance
book_router = BookServiceRouter().router 