import logging
import os
from datetime import datetime

import httpx

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            f'logs/recommendation_service_{datetime.now().strftime("%Y%m%d")}.log'
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("recommendation_service")

SHARED_SERVICE_URL = os.getenv("SHARED_SERVICE_URL", "http://localhost:8000")


async def log_action(user_id: str, action: str, status: str, details: str = None):
    """
    Log an action to both the application log and shared service.

    Args:
        user_id: ID of the user performing the action
        action: The action being performed
        status: Status of the action (success/failure)
        details: Additional details about the action
    """
    try:
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
                response = await client.post(
                    f"{SHARED_SERVICE_URL}/api/v1/logs",
                    json={
                        "user_id": user_id,
                        "action": action,
                        "status": status,
                        "details": details,
                    },
                )
                if response.status_code != 200:
                    logger.error(f"Failed to log action: {response.text}")
        except Exception as e:
            logger.error(f"Failed to send log to shared service: {str(e)}")
            # Don't raise the exception as logging should not break the main functionality

    except Exception as e:
        logger.error(f"Error logging action: {str(e)}")
        # Don't raise the exception as logging should not break the main functionality
