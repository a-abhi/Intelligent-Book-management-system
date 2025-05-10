from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import logging
from models import Preference
from schemas import PreferenceCreate, PreferenceResponse, BookRecommendation
from db import get_db
from utils.auth import verify_auth
from utils.logging import log_action
from utils.book import get_books_by_genre

logger = logging.getLogger(__name__)

class RecommendationServiceRouter:
    def __init__(self):
        self.router = APIRouter(prefix="/api/v1", tags=["recommendations"])
        self.security = HTTPBasic()
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up all routes for the recommendation service."""   
        @self.router.post("/preferences", response_model=PreferenceResponse)
        async def create_preference(
            preference: PreferenceCreate,
            db: AsyncSession = Depends(get_db),
            user_id: uuid.UUID = Depends(verify_auth)
        ):
            try:
                # Create preference
                db_preference = Preference(
                    user_id=user_id,
                    genre=preference.genre
                )
                db.add(db_preference)
                await db.commit()
                await db.refresh(db_preference)
                
                # Log success
                await log_action(str(user_id), "create_preference", "success", f"Created preference for genre {preference.genre}")
                return db_preference
                
            except Exception as e:
                await log_action(str(user_id), "create_preference", "error", str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while creating the preference"
                )

        @self.router.get("/preferences", response_model=List[PreferenceResponse])
        async def get_preferences(
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth)
        ):
            try:
                stmt = select(Preference).where(Preference.user_id == user_id)
                result = await db.execute(stmt)
                preferences = result.scalars().all()
                
                await log_action(str(user_id), "get_preferences", "success", f"Retrieved {len(preferences)} preferences")
                return preferences
            except Exception as e:
                await log_action(str(user_id), "get_preferences", "error", str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while retrieving preferences"
                )

        @self.router.get("/recommendations", response_model=List[BookRecommendation])
        async def get_recommendations(
            db: AsyncSession = Depends(get_db),
            user_id: int = Depends(verify_auth),
            credentials: HTTPBasicCredentials = Depends(security)
        ):
            try:
                # Get user preferences
                stmt = select(Preference).where(Preference.user_id == user_id)
                result = await db.execute(stmt)
                preferences = result.scalars().all()
                
                if not preferences:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No preferences found for user"
                    )
                
                # Get recommendations based on preferences
                seen_books = set()  # Track unique book IDs
                recommendations = []
                
                for preference in preferences:
                    books = await get_books_by_genre(preference.genre, (credentials.username, credentials.password))
                    for book in books:
                        # Only add book if we haven't seen it before
                        if book["id"] not in seen_books:
                            seen_books.add(book["id"])
                            recommendations.append(book)
                
                # Log success
                await log_action(str(user_id), "get_recommendations", "success", f"Retrieved {len(recommendations)} unique recommendations")
                return recommendations
                
            except HTTPException as e:
                await log_action(str(user_id), "get_recommendations", "error", str(e.detail))
                raise e
            except Exception as e:
                await log_action(str(user_id), "get_recommendations", "error", str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while getting recommendations"
                )


        @self.router.get("/health")
        async def health_check():
            return {"status": "healthy"} 

# Create router instance
recommendation_router = RecommendationServiceRouter().router 