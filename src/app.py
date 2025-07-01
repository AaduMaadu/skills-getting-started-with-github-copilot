"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from pymongo import MongoClient
from typing import Dict, Any

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# MongoDB connection
MONGODB_URL = "mongodb://localhost:27017/"
DATABASE_NAME = "mergington_school"
COLLECTION_NAME = "activities"

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
activities_collection = db[COLLECTION_NAME]

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# Initial activity data for database seeding
INITIAL_ACTIVITIES = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    # Sports activities
    "Soccer Team": {
        "description": "Join the school soccer team and compete in local leagues",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["lucas@mergington.edu", "mia@mergington.edu"]
    },
    "Basketball Club": {
        "description": "Practice basketball skills and play friendly matches",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["liam@mergington.edu", "ava@mergington.edu"]
    },
    # Artistic activities
    "Art Club": {
        "description": "Explore painting, drawing, and other visual arts",
        "schedule": "Mondays, 3:30 PM - 5:00 PM",
        "max_participants": 18,
        "participants": ["noah@mergington.edu", "isabella@mergington.edu"]
    },
    "Drama Society": {
        "description": "Participate in acting, stage production, and school plays",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 25,
        "participants": ["ethan@mergington.edu", "charlotte@mergington.edu"]
    },
    # Intellectual activities
    "Debate Club": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 16,
        "participants": ["amelia@mergington.edu", "benjamin@mergington.edu"]
    },
    "Math Olympiad": {
        "description": "Prepare for math competitions and solve challenging problems",
        "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["elijah@mergington.edu", "harper@mergington.edu"]
    }
}

def initialize_database():
    """Initialize the database with activity data if it's empty"""
    try:
        # Check if activities already exist
        if activities_collection.count_documents({}) == 0:
            print("Seeding database with initial activities...")
            
            # Insert activities with name as the _id for easy querying
            documents = []
            for activity_name, activity_data in INITIAL_ACTIVITIES.items():
                doc = {
                    "_id": activity_name,
                    "name": activity_name,
                    **activity_data
                }
                documents.append(doc)
            
            activities_collection.insert_many(documents)
            print(f"Inserted {len(documents)} activities into the database.")
        else:
            print("Database already contains activities, skipping initialization.")
    except Exception as e:
        print(f"Error initializing database: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    initialize_database()

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    client.close()

# Add a health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Ping MongoDB
        client.admin.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# Initialize database on startup
initialize_database()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    """Get all activities from MongoDB"""
    activities = {}
    for activity in activities_collection.find():
        activity_name = activity["_id"]
        # Remove MongoDB specific fields for clean response
        activity_data = {k: v for k, v in activity.items() if k not in ["_id", "name"]}
        activities[activity_name] = activity_data
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    activity = activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    # Validate capacity
    if len(activity["participants"]) >= activity["max_participants"]:
        raise HTTPException(status_code=400, detail="Activity is at maximum capacity")

    # Add student to activity
    activities_collection.update_one(
        {"_id": activity_name},
        {"$push": {"participants": email}}
    )
    
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/participants/{email}")
def remove_participant(activity_name: str, email: str):
    """Remove a student from an activity"""
    # Validate activity exists
    activity = activities_collection.find_one({"_id": activity_name})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(status_code=404, detail="Student not found in activity")

    # Remove student from activity
    activities_collection.update_one(
        {"_id": activity_name},
        {"$pull": {"participants": email}}
    )
    
    return {"message": f"Removed {email} from {activity_name}"}
