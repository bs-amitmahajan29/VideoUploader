from fastapi import FastAPI, HTTPException, Header
import json

with open('config/config.json') as config_file:
    config = json.load(config_file)

API_TOKENS = config['api_token']

# Initialize app
app = FastAPI()

def authenticate(api_token: str = Header(None)):
    if not api_token:
        raise HTTPException(status_code=401, detail="Unauthorized: Missing api_token")
    if api_token not in API_TOKENS:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid API token")
    return True

@app.post("/check_api_token")
async def check_api_token(api_token: str = Header(None)):
    authorized = authenticate(api_token)
    return {"Authorized": authorized}

