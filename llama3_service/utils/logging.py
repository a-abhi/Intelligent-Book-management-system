import logging
import os
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession


# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/llama3_service.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("llama3_service")

SHARED_SERVICE_URL = os.getenv("SHARED_SERVICE_URL", "http://localhost:8000")

def setup_logging():
    """Configure logging for the application."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

async def log_action(
    user_id: str,
    action: str,
    status: str,
    details: str = None
):
    """
    Log an action to both file and shared service.
    
    Args:
        user_id: ID of the user performing the action
        action: Name of the action
        status: Status of the action (success/failure)
        details: Additional details about the action
    """
    try:
        # Log to file
        log_message = f"User {user_id} - {action} - {status}"
        if details:
            log_message += f" - {details}"
        logger.info(log_message)
        
        # Log to shared service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SHARED_SERVICE_URL}/api/v1/logs",
                json={
                    "user_id": user_id,
                    "action": action,
                    "status": status,
                    "details": details
                }
            )
            if response.status_code != 200:
                logger.error(f"Failed to log action: {response.text}")
            
    except Exception as e:
        # Don't let logging failures affect the main functionality
        logger.error(f"Error logging action: {str(e)}")