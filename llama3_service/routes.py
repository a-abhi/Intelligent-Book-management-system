from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import BookSummary
from schemas import (
    BookSummaryCreate,
    BookSummaryResponse,
    ReviewSummaryRequest,
    ReviewSummaryResponse
)
from db import get_db
from utils.auth import verify_auth
from utils.logging import log_action, logger
from utils.book import verify_book_exists
import httpx
import os
from typing import Optional

class Llama3ServiceRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1", tags=["llama3"])
        self.security = HTTPBasic()
        self.LLAMA_API_URL = os.getenv("LLAMA_API_URL", "http://localhost:11434")
        self.LLAMA_MODEL = os.getenv("LLAMA_MODEL", "llama3.2")
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up all routes for the llama3 service."""
        self.router.add_api_route(
            "/generate-summary",
            self.generate_summary,
            methods=["POST"],
            response_model=BookSummaryResponse
        )
        self.router.add_api_route(
            "/summaries/{book_id}",
            self.get_summary,
            methods=["GET"],
            response_model=BookSummaryResponse
        )
        self.router.add_api_route(
            "/generate-review-summary",
            self.generate_review_summary,
            methods=["POST"],
            response_model=ReviewSummaryResponse
        )
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"]
        )
    
    async def get_cached_summary(
        self,
        db: AsyncSession,
        book_id: int,
        user_id: int,
    ) -> Optional[BookSummary]:
        """Get a cached summary for the given book_id and user_id if it exists."""
        stmt = select(BookSummary).where(
            BookSummary.book_id == book_id,
            BookSummary.user_id == user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    def _create_summary_response(self, summary: BookSummary) -> BookSummaryResponse:
        """Helper function to create BookSummaryResponse from BookSummary model."""
        return BookSummaryResponse(
            id=summary.id,
            book_id=summary.book_id,
            content=summary.content,
            summary=summary.summary,
            created_at=summary.created_at,
            updated_at=summary.updated_at
        )
    
    async def _generate_summary(self, content: str) -> str:
        """Generate a summary using the Llama model."""
        prompt = f"Please provide a concise summary of the following text:\n\n{content}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.LLAMA_API_URL}/api/generate",
                    json={
                        "model": self.LLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "max_tokens": 500    # Limit response length
                    }
                )
                
                if response.status_code != 200:
                    error_detail = f"Ollama API error: Status {response.status_code}, Response: {response.text}"
                    logger.error(error_detail)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=error_detail
                    )
                
                response_data = response.json()
                logger.info(f"Ollama API response: {response_data}")
                
                if "response" not in response_data:
                    error_detail = f"Unexpected Ollama API response format: {response_data}"
                    logger.error(error_detail)
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=error_detail
                    )
                
                return response_data["response"]
                
        except httpx.RequestError as e:
            error_detail = f"Failed to connect to Ollama API: {str(e)}"
            logger.error(error_detail)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=error_detail
            )
        except Exception as e:
            error_detail = f"Unexpected error during summary generation: {str(e)}"
            logger.error(error_detail)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_detail
            )
    
    async def generate_summary(
        self,
        request: BookSummaryCreate,
        refresh: bool = False,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(verify_auth),
        credentials: HTTPBasicCredentials = Depends(HTTPBasic())
    ):
        """Generate or retrieve a summary for a book."""
        try:
            # Verify book exists before proceeding
            book_exists = await verify_book_exists(request.book_id, (credentials.username, credentials.password))
            if not book_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Book with ID {request.book_id} not found"
                )
            
            # Check if summary exists in database
            existing_summary = await self.get_cached_summary(db, request.book_id, user_id)
            
            # Return cached summary if it exists and refresh is False
            if existing_summary and not refresh:
                await log_action(
                    user_id=str(user_id),
                    action="get_summary",
                    status="success",
                    details=f"Retrieved cached summary for book {request.book_id}"
                )
                return self._create_summary_response(existing_summary)
            
            # Generate new summary
            summary = await self._generate_summary(request.content)
            
            if existing_summary:
                # Update existing summary
                existing_summary.content = request.content
                existing_summary.summary = summary
                await db.commit()
                await db.refresh(existing_summary)
                
                await log_action(
                    user_id=str(user_id),
                    action="update_summary",
                    status="success",
                    details=f"Updated summary for book {request.book_id}"
                )
                return self._create_summary_response(existing_summary)
            
            # Create new summary
            db_summary = BookSummary(
                book_id=request.book_id,
                user_id=user_id,
                content=request.content,
                summary=summary
            )
            db.add(db_summary)
            await db.commit()
            await db.refresh(db_summary)
            
            await log_action(
                user_id=str(user_id),
                action="create_summary",
                status="success",
                details=f"Created summary for book {request.book_id}"
            )
            return self._create_summary_response(db_summary)
            
        except HTTPException:
            raise
        except Exception as e:
            await log_action(
                user_id=str(user_id),
                action="generate_summary",
                status="error",
                details=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while generating summary"
            )
    
    async def get_summary(
        self,
        book_id: int,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(verify_auth)
    ):
        """Get a summary for a specific book."""
        try:
            stmt = select(BookSummary).where(
                BookSummary.book_id == book_id,
                BookSummary.user_id == user_id
            )
            result = await db.execute(stmt)
            summary = result.scalar_one_or_none()
            
            if not summary:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Summary not found"
                )
            
            await log_action(
                user_id=str(user_id),
                action="get_summary",
                status="success",
                details=f"Retrieved summary for book {book_id}"
            )
            
            return self._create_summary_response(summary)
            
        except HTTPException:
            raise
        except Exception as e:
            await log_action(
                user_id=str(user_id),
                action="get_summary",
                status="error",
                details=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while retrieving the summary"
            )
    
    async def generate_review_summary(
        self,
        request: ReviewSummaryRequest,
        db: AsyncSession = Depends(get_db),
        user_id: int = Depends(verify_auth),
        credentials: HTTPBasicCredentials = Depends(HTTPBasic())
    ):
        """Generate a summary of reviews for a book."""
        try:
            # Verify book exists
            book_exists = await verify_book_exists(request.book_id, (credentials.username, credentials.password))
            if not book_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Book with ID {request.book_id} not found"
                )
            
            # Generate summary
            summary = await self._generate_summary(request.content)
            
            await log_action(
                user_id=str(user_id),
                action="generate_review_summary",
                status="success",
                details=f"Generated review summary for book {request.book_id}"
            )
            
            return ReviewSummaryResponse(
                book_id=request.book_id,
                summary=summary
            )
            
        except HTTPException:
            raise
        except Exception as e:
            await log_action(
                user_id=str(user_id),
                action="generate_review_summary",
                status="error",
                details=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while generating review summary"
            )
    
    async def health_check(self):
        """Check the health status of the llama3 service."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.LLAMA_API_URL}/api/tags")
                if response.status_code == 200:
                    return {"status": "healthy", "model": self.LLAMA_MODEL}
                else:
                    return {"status": "unhealthy", "error": "Ollama API not responding"}
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}

# Create router instance
llama3_router = Llama3ServiceRouter().router 