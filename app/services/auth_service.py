from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Initialize the HTTPBearer security scheme
security = HTTPBearer()

class APIKeyAuth:
    def __init__(self):
        self.api_keys = settings.api_keys_list
        self.enabled = settings.API_KEY_ENABLED
        logger.info(f"API Authentication initialized. Enabled: {self.enabled}, Keys loaded: {len(self.api_keys)}")
    
    async def authenticate(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """
        Authenticate API key from Bearer token
        
        Args:
            credentials: HTTPAuthorizationCredentials from FastAPI security
            
        Returns:
            str: The validated API key
            
        Raises:
            HTTPException: If authentication fails
        """
        if not self.enabled:
            logger.debug("API key authentication is disabled")
            return "disabled"
        
        if not credentials:
            logger.warning("No authorization credentials provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract the token (remove 'Bearer ' prefix if present)
        token = credentials.credentials
        
        if not token:
            logger.warning("Empty token provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate the token against our API keys
        if token not in self.api_keys:
            logger.warning(f"Invalid API key attempted: {token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"API key authenticated successfully: {token[:10]}...")
        return token
    
    def get_dependency(self):
        """
        Get the FastAPI dependency for authentication
        
        Returns:
            Callable: Dependency function for FastAPI routes
        """
        if self.enabled:
            return Depends(self.authenticate)
        else:
            # Return a dummy dependency that always passes
            return Depends(lambda: "disabled")

# Global instance
api_auth = APIKeyAuth()

# Convenience function to get the dependency
def get_api_key_dependency():
    """Get the API key dependency for route protection"""
    return api_auth.get_dependency()

# Alternative function for manual key validation (without FastAPI dependency)
def validate_api_key_manual(api_key: str) -> bool:
    """
    Manually validate an API key
    
    Args:
        api_key: The API key to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not settings.API_KEY_ENABLED:
        return True
    
    return api_key in settings.api_keys_list
