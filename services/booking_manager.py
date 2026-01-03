import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid

# Load data
DEVICES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'devices.json')
try:
    with open(DEVICES_FILE, 'r') as f:
        DEVICES_DATA = json.load(f)
except FileNotFoundError:
    DEVICES_DATA = []

# Import mock booking store
from data.bookings_store import BOOKED_SESSIONS

def get_devices(campus_id: Optional[int] = None, device_code: Optional[str] = None) -> List[Dict]:
    """
    Returns a list of devices, optionally filtered by campus_id or device_code (partial match).
    """
    results = DEVICES_DATA
    
    if campus_id:
        results = [d for d in results if d['CampusId'] == campus_id]
    
    if device_code:
        # Simple case-insensitive partial match
        results = [d for d in results if device_code.lower() in d['DeviceCode'].lower()]
        
    return results

def get_booked_sessions(device_ids: List[int], start_date: str, end_date: str) -> List[Dict]:
    """
    Returns booked sessions for the specific devices within the date range.
    Enforces the rule: only return sessions for future dates up to 3 months.
    """
    # Parse dates
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        return []

    now = datetime.now()
    max_future = now + timedelta(days=90) # 3 months approx

    # Filter mock store
    relevant_sessions = []
    for session in BOOKED_SESSIONS:
        if session['device_id'] in device_ids:
            sess_start = datetime.fromisoformat(session['start_time'])
            
            # Check constraints
            if sess_start < now:
                continue # Skip past sessions
            if sess_start > max_future:
                continue # Skip sessions beyond 3 months
                
            # Check range overlap
            # Overlap if (StartA <= EndB) and (EndA >= StartB)
            # Here we just check if it falls within the requested range broadly
            sess_end = datetime.fromisoformat(session['end_time'])
            
            if sess_start >= start_dt and sess_end <= end_dt:
                relevant_sessions.append(session)
                
    return relevant_sessions

def get_availability(device_id: int, date_str: str) -> List[Dict]:
    """
    Returns available 4-hour slots for a specific device on a specific date.
    Logic: Dynamic gap calculation.
    1. Fetch all bookings for the day.
    2. Identify free time ranges.
    3. Generate 4-hour slots within those free ranges.
    """
    base_date = datetime.fromisoformat(date_str).date()
    # Define Day Boundaries (00:00 to 24:00)
    day_start = datetime.combine(base_date, datetime.min.time())
    day_end = day_start + timedelta(days=1)
    
    # Get bookings
    booked = get_booked_sessions([device_id], day_start.isoformat(), day_end.isoformat())
    
    # Sort bookings by start time
    booked_intervals = []
    for b in booked:
        start = datetime.fromisoformat(b['start_time'])
        end = datetime.fromisoformat(b['end_time'])
        # Clip to day boundaries logic if needed, but for now take as is
        booked_intervals.append((start, end))
    booked_intervals.sort(key=lambda x: x[0])
    
    # Find Gaps
    free_gaps = []
    current_pointer = day_start
    
    for b_start, b_end in booked_intervals:
        if b_start > current_pointer:
            free_gaps.append((current_pointer, b_start))
        current_pointer = max(current_pointer, b_end)
        
    if current_pointer < day_end:
        free_gaps.append((current_pointer, day_end))
        
    # Generate 4-hour slots from gaps
    available_slots = []
    now = datetime.now()
    
    for gap_start, gap_end in free_gaps:
        # We try to fit 4h blocks. 
        # Strategy: Greedy. Start at gap_start.
        # Alternative: Rolling every hour?
        # User req: "Each slot should be of duration of 4 hours".
        # Let's offer slots at regular intervals (e.g. every hour) if they fit.
        
        # Check iteratively every hour within the gap
        slot_start = gap_start
        while slot_start + timedelta(hours=4) <= gap_end:
            slot_end = slot_start + timedelta(hours=4)
            
            # Additional constraint: Must be in future
            if slot_start > now:
                available_slots.append({
                    "start": slot_start.isoformat(),
                    "end": slot_end.isoformat(),
                    "label": f"{slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
                })
            
            # Step size: 1 hour (to give options) or 4 hours (non-overlapping)?
            # Regular booking systems usually offer slots every 30min or 1h. 
            # Prompt says "fill 3 slots per day", "leave remaining empty". 
            # Let's provide non-overlapping if possible, OR overlapping options.
            # "show the available duration". 
            # Let's do overlapping options every 1 hour to maximize user choice within the gap.
            slot_start += timedelta(hours=1)
            
    return available_slots

def book_sessions(cart_items: List[Dict]) -> Dict:
    """
    Books the sessions in the cart.
    Updates the mock store.
    Returns confirmation details.
    """
    confirmation_number = f"CONF-{uuid.uuid4().hex[:8].upper()}"
    new_bookings = []
    
    for item in cart_items:
        booking = {
            "booking_id": f"{confirmation_number}-{item['DeviceId']}",
            "device_id": item['DeviceId'],
            "start_time": item['SlotStart'],
            "end_time": item['SlotEnd'],
            "customer_code": "USER_WEB", # Placeholder
            "training_type": "Training"
        }
        BOOKED_SESSIONS.append(booking)
        new_bookings.append(booking)
        
    return {
        "status": "success",
        "confirmation_number": confirmation_number,
        "booked_count": len(new_bookings)
    }
