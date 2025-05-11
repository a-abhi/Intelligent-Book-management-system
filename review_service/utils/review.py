import os
from typing import List

import httpx
from fastapi import HTTPException, status

from models import Review
from utils.logging import logger

LLAMA3_SERVICE_URL = os.getenv("LLAMA3_SERVICE_URL", "http://localhost:8004")


async def generate_book_reviews_summary(reviews: List[Review], auth: tuple) -> str:
    """
    Call the LLaMA3 service to generate a summary for all reviews of a book.

    Args:
        reviews: List of Review objects for the book
        auth: Tuple of (username, password) for authentication

    Returns:
        Generated summary

    Raises:
        HTTPException: If the LLaMA3 service call fails
    """
    try:
        if not reviews:
            return "No reviews available for this book."

        # Calculate average rating
        avg_rating = sum(r.rating for r in reviews) / len(reviews)

        # Prepare the content for summarization
        content = "Book Reviews Summary\n"
        content += f"Average Rating: {avg_rating:.1f}/5\n"
        content += f"Total Reviews: {len(reviews)}\n\n"
        content += "Individual Reviews:\n"

        for review in reviews:
            content += f"\nRating: {review.rating}/5\n"
            if review.comment:
                content += f"Review: {review.comment}\n"

        logger.info(
            f"Generating summary for book {reviews[0].book_id} with {len(reviews)} reviews"
        )
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LLAMA3_SERVICE_URL}/api/v1/generate-review-summary",
                json={"book_id": reviews[0].book_id, "content": content},
                auth=auth,
            )

            if response.status_code == 200:
                return response.json()["summary"]
            elif response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed with LLaMA3 service",
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error generating summary",
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLaMA3 service is unavailable",
        )
