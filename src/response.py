from pydantic import BaseModel
from typing import Any, Optional

class ApiResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    data: Optional[Any] = None
    
def create_response(success: bool, message: str = None, data: Any = None):
    return {
        "success": success,
        "message": message,
        "data": data
    }