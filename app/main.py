from fastapi import FastAPI, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from itsdangerous import URLSafeTimedSerializer, BadSignature
from . import crud, models
from .database import engine, Base, get_db
from .auth import hash_password, verify_password
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
import joblib
import pandas as pd
import uvicorn


from pathlib import Path




import cv2
import numpy as np
import pytesseract
from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
import io
from .Processing_Model import process_image
from fastapi.middleware.cors import CORSMiddleware


BASE_DIR = Path(__file__).resolve().parent.parent
print(BASE_DIR)

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create database tables


# Secret key for session management
SECRET_KEY = "dsvsdghvds9s49d-sf9s-s7f-9s4f-8sdf4"
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Configure Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

def get_username_from_session(request: Request):
    session_cookie = request.cookies.get("session")
    if session_cookie:
        try:
            session_data = serializer.loads(session_cookie, max_age=3600)  # 1 hour session expiration
            return session_data.get("username")
        except BadSignature:
            return None
    return None

def verify_session(request: Request):
    username = get_username_from_session(request)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access. Please log in."
        )
    return username

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    username = get_username_from_session(request)
    return templates.TemplateResponse("index.html", {"request": request, "username": username})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request, username: str = Depends(verify_session)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "username": username})



@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        print(f"Attempting to register user with email: {email}")

        # Check if user already exists
        db_user = crud.get_user_by_email(db, email=email)
        if db_user:
            print("User already exists with this email")
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash the password before storing it
        hashed_password = hash_password(password)
        user = models.User(username=username, email=email, hashed_password=hashed_password)

        # Add user to the database
        db.add(user)
        db.commit()
        db.refresh(user)

        print("User registered successfully")
        return templates.TemplateResponse("login.html", {"request": request, "msg": "Registration successful! Please log in."})
    except Exception as e:
        print(f"Error during registration: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/login", response_class=HTMLResponse)
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        print(f"Attempting to log in with email: {email}")

        db_user = crud.get_user_by_email(db, email=email)
        if not db_user:
            print("User not found")
            raise HTTPException(status_code=400, detail="Invalid credentials")

        if not verify_password(password, db_user.hashed_password):
            print("Password does not match")
            raise HTTPException(status_code=400, detail="Invalid credentials")

        session_data = {"username": db_user.username}
        session_cookie = serializer.dumps(session_data)

        response = RedirectResponse(url="/identity", status_code=status.HTTP_302_FOUND)
        # response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="session", value=session_cookie, httponly=True)
        return response
    except Exception as e:
        print(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.get("/logout")
def logout(request: Request):
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("session")
    return response












@app.get("/identity", response_class=HTMLResponse)
def identity_page(request: Request, username: str = Depends(verify_session)):
    return templates.TemplateResponse("identity.html", {"request": request, "username": username})




@app.post("/verify")
async def verify(
    first_name: str = Form(...),
    last_name: str = Form(...),
    surname: str = Form(...),
    pan_number: str = Form(...),
    image: UploadFile = File(...)
):
    image_bytes = await image.read()
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

    if image.shape[1] != 880 or image.shape[0] != 495:
        return JSONResponse(content={"message": "Image size must be 880 x 495."}, status_code=400)
    

    ref_img_location = f"{BASE_DIR}\\app\\static\\assets\\img\\Images\\pancard_blank_.png"
    data = process_image(image,ref_img_location)

    if not data:
        return JSONResponse(content={"message": "Failed to extract data from the image."}, status_code=400)

    extracted_first_name, extracted_last_name, extracted_surname, extracted_pan_number = data

    if (first_name.upper() == extracted_first_name and
        last_name.upper() == extracted_last_name and
        surname.upper() == extracted_surname and 
        pan_number.upper() == extracted_pan_number):
        
        return {"message": "Your information matches."} 
    else:
        return {"message": "Your information does not match."}
    
    # #################   ML Prediction ###############

#     uvicorn app.main:app --reload
model = joblib.load(f"{BASE_DIR}\\app\\static\\loan_approval_model_2.pkl")

# Define a request model
class LoanRequest(BaseModel):
    age: int
    income_annum: float
    work_exp: int
    credit_score: int
    loan_amount: float
    loan_term: int
    employment_status: str
    marital_status: str
    property_area: str
    residential_assets_value: float
    commercial_assets_value: float
    luxury_assets_value: float
    bank_asset_value: float
    dti: float
    previous_loan_history: str

# Define a route to handle predictions
@app.post('/predict')
async def predict(request: LoanRequest):
    try:
        # Convert request to DataFrame
        data = pd.DataFrame([request.dict()])

        # Make prediction
        prediction = model.predict(data)
        print(prediction[0])

        return {'prediction': prediction[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
