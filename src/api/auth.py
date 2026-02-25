from fastapi import APIRouter, HTTPException
from src.models.schemas import LoginRequest, UserResponse
from src.models.mongodb import UserDoc
from src.core.database import db
from src.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/login", response_model=UserResponse)
async def login(request: LoginRequest):
    logger.info(f"Login request for mobile: {request.mobile_number}")
    
    users_col = db.db["users"]
    
    # Try to find existing user
    user_data = await users_col.find_one({"mobile_number": request.mobile_number})
    
    if not user_data:
        # Create new user if not exists
        logger.info(f"Creating new user for mobile: {request.mobile_number}")
        user = UserDoc(mobile_number=request.mobile_number)
        await users_col.insert_one(user.model_dump())
        return UserResponse(
            id=user.id, 
            mobile_number=user.mobile_number,
            name=user.name,
            role=user.role
        )
    
    return UserResponse(
        id=user_data["id"], 
        mobile_number=user_data["mobile_number"],
        name=user_data.get("name", "Anonymous"),
        role=user_data.get("role", "User")
    )
