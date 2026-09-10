"""
Learning Routes
===============
API endpoints for fetching learning materials and roadmaps.
"""

from fastapi import APIRouter, HTTPException
import json
import os
from typing import List, Dict, Any

router = APIRouter()

DATA_DIR = "data/learning"

@router.get("/learning/branches")
def get_branches():
    """Get all available engineering branches"""
    try:
        with open(f"{DATA_DIR}/index.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading branches: {e}")
        return {"branches": []}

@router.get("/learning/{branch_id}")
def get_branch_topics(branch_id: str):
    """Get topics for a specific branch (e.g., cse, ece)"""
    try:
        path = f"{DATA_DIR}/{branch_id}/index.json"
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Branch not found")
            
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error loading branch topics: {e}")
        return {"topics": []}

@router.get("/learning/{branch_id}/{topic_id}")
def get_topic_notes(branch_id: str, topic_id: str):
    """Get detailed notes for a specific topic"""
    try:
        path = f"{DATA_DIR}/{branch_id}/{topic_id}.json"
        if not os.path.exists(path):
            # Try finding it without extension or different case if needed
            # For now, just return 404
            raise HTTPException(status_code=404, detail="Topic notes not found")
            
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error loading topic notes: {e}")
        return {"notes": []}
