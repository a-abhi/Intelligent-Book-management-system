import logging
import os
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert


# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/book_service_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("book_service")

SHARED_SERVICE_URL = os.getenv("SHARED_SERVICE_URL", "http://localhost:8000")

async def log_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    status: str,
    details: str = None
):
    """
    Log an action to both the application log, local database, and shared service.
    
    Args:
        db: Database session
        user_id: ID of the user performing the action
        action: The action being performed
        status: Status of the action (success/failure)
        details: Additional details about the action
    """
    try:
        # Create log entry
        log_entry = {
            "user_id": user_id,
            "action": action,
            "status": status,
            "details": details,
            "created_at": datetime.utcnow()
        }
        
        # Insert into local database
        stmt = insert(Log).values(**log_entry)
        await db.execute(stmt)
        await db.commit()
        
        # Log to file
        log_message = f"User {user_id} performed {action} with status {status}"
        if details:
            log_message += f" - Details: {details}"
            
        if status == "success":
            logger.info(log_message)
        else:
            logger.error(log_message)
            
        # Send to shared service
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{SHARED_SERVICE_URL}/logs",
                    json={
                        "user_id": user_id,
                        "service": "book_service",
                        "action": action,
                        "status": status,
                        "details": details
                    }
                )
        except Exception as e:
            logger.error(f"Failed to send log to shared service: {str(e)}")
            # Don't raise the exception as logging should not break the main functionality
            
    except Exception as e:
        logger.error(f"Error logging action: {str(e)}")
        # Don't raise the exception as logging should not break the main functionality 