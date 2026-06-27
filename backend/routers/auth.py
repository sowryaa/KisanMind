from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests
import os

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

class GoogleAuthRequest(BaseModel):
    token: str

@router.post("/google")
async def google_auth(auth_req: GoogleAuthRequest):
    """Verify Google OAuth token and return user details."""
    try:
        # Verify the token against Google
        id_info = id_token.verify_oauth2_token(
            auth_req.token, 
            requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # User details from token
        userid = id_info['sub']
        email = id_info.get('email')
        name = id_info.get('name')
        picture = id_info.get('picture')
        
        return {
            "status": "success",
            "user": {
                "google_id": userid,
                "email": email,
                "name": name,
                "avatar_url": picture
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
