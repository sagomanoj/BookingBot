from datetime import datetime, timedelta

# In-memory store for booked sessions
# Structure:
# [
#     {
#         "booking_id": "CONF-123",
#         "device_id": 101,
#         "start_time": "2023-12-25T00:00:00",
#         "end_time": "2023-12-25T04:00:00",
#         "customer_code": "CUST001",
#         "training_type": "Training"
#     },
#     ...
# ]

BOOKED_SESSIONS = []

def init_mock_bookings():
    """
    Pre-fills the BOOKED_SESSIONS list with some mock data for the next few days.
    We are simulating that slots 3AM-7AM (03:00-07:00), 8AM-12PM (08:00-12:00), 
    1PM-5PM (13:00-17:00) are booked for testing purposes.
    """
    global BOOKED_SESSIONS
    # Clear existing to avoid duplicates on re-run if this was a real db connection
    BOOKED_SESSIONS = []
    
    today = datetime.now().date()
    
    # Generate mock bookings for the next 7 days for a few devices
    device_ids = [101, 102, 201, 301] # Just picking a few active ones
    
    for i in range(7):
        current_date = today + timedelta(days=i)
        date_str = current_date.isoformat()
        
        for dev_id in device_ids:
            # Slot 1: 03:00 - 07:00 -> Technically fits 00:00-04:00 and 04:00-08:00 partially if we use fixed blocks.
            # But prompt says "slots are booked" and "duration is 4 hours".
            # Let's align with the prompt's implied fixed structure if possible, 
            # OR just strictly use time ranges. 
            # Requirement: "each sessions duration is of 4 hours".
            # The prompt example: "3AM to 7AM and 8AM to 12PM, 1PM to 5PM slots are booked."
            # That's 4h duration sessions.
            
            # Booking 1
            BOOKED_SESSIONS.append({
                "booking_id": f"MOCK-{dev_id}-{i}-1",
                "device_id": dev_id,
                "start_time": f"{date_str}T03:00:00",
                "end_time": f"{date_str}T07:00:00",
                "customer_code": "AIRLINE-A",
                "training_type": "Training"
            })
            
            # Booking 2
            BOOKED_SESSIONS.append({
                "booking_id": f"MOCK-{dev_id}-{i}-2",
                "device_id": dev_id,
                "start_time": f"{date_str}T08:00:00",
                "end_time": f"{date_str}T12:00:00",
                "customer_code": "AIRLINE-B",
                "training_type": "Maintenance"
            })
            
            # Booking 3
            BOOKED_SESSIONS.append({
                "booking_id": f"MOCK-{dev_id}-{i}-3",
                "device_id": dev_id,
                "start_time": f"{date_str}T13:00:00",
                "end_time": f"{date_str}T17:00:00",
                "customer_code": "AIRLINE-C",
                "training_type": "Training"
            })

# Initialize on module load
init_mock_bookings()
