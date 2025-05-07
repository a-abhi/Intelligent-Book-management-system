import logging
import sys
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/shared_service_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger("shared_service")

def log_request(
    endpoint: str,
    method: str,
    status_code: int,
    user_id: Optional[str] = None,
    error: Optional[str] = None
):
    """Log API request details"""
    log_data = {
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if error:
        log_data["error"] = error
        logger.error(f"API Request: {log_data}")
    else:
        logger.info(f"API Request: {log_data}")

def log_error(
    endpoint: str,
    error: Exception,
    user_id: Optional[str] = None
):
    """Log error details"""
    log_data = {
        "endpoint": endpoint,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    logger.error(f"Error occurred: {log_data}")
