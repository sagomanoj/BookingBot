import requests
import os
from typing import List, Dict, Optional

# Default to local dev server if not set
API_BASE_URL = os.getenv('SIMULATOR_API_URL', 'http://127.0.0.1:5000/api')

def get_devices(campus_id: Optional[int] = None, device_code: Optional[str] = None) -> List[Dict]:
    """
    Fetches devices from the API.
    """
    params = {}
    if campus_id: params['campus_id'] = campus_id
    if device_code: params['device_code'] = device_code
    
    try:
        response = requests.get(f"{API_BASE_URL}/devices", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API Error (get_devices): {e}")
        return []

def get_booked_sessions(device_ids: List[int], start_date: str, end_date: str) -> List[Dict]:
    """
    Fetches booked sessions from the API.
    """
    payload = {
        "device_ids": device_ids,
        "start_date": start_date,
        "end_date": end_date
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/booked_sessions", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API Error (get_booked_sessions): {e}")
        return []

def get_availability(device_id: int, date: str) -> List[Dict]:
    """
    Fetches availability from the API.
    """
    params = {
        "device_id": device_id,
        "date": date
    }
    
    try:
        response = requests.get(f"{API_BASE_URL}/availability", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API Error (get_availability): {e}")
        return []

def book_sessions(cart_items: List[Dict]) -> Dict:
    """
    Sends booking request to the API.
    """
    payload = {"cart": cart_items}
    
    try:
        response = requests.post(f"{API_BASE_URL}/book", json=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"API Error (book_sessions): {e}")
        return {"status": "error", "message": str(e)}
