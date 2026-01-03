from services import booking_service
from datetime import datetime, timedelta

def run_tests():
    print("--- 1. Testing Device Listing ---")
    devices = booking_service.get_devices(campus_id=1)
    print(f"Found {len(devices)} devices in Miami (Campus 1).")
    for d in devices:
        print(f" - {d['DeviceCode']}: {d['DeviceName']}")
        
    print("\n--- 2. Testing Availability ---")
    # Pick a device
    device_id = devices[0]['DeviceId']
    
    # Test date: Today
    today = (datetime.now() + timedelta(days=1)).date().isoformat()
    print(f"Checking availability for Device {device_id} on {today} (Tomorrow)...")
    
    slots = booking_service.get_availability(device_id, today)
    print(f"Available slots: {len(slots)}")
    for s in slots:
        print(f" [{s['start']} - {s['end']}]")
        
    print("\n--- 3. Testing Booking ---")
    if slots:
        target_slot = slots[0]
        cart = [{
            "DeviceId": device_id,
            "SlotStart": target_slot['start'],
            "SlotEnd": target_slot['end'],
            "Label": target_slot['label'],
            "Date": today
        }]
        
        print(f"Booking slot: {target_slot['label']}")
        result = booking_service.book_sessions(cart)
        print("Booking Result:", result)
        
        # Verify it is now gone
        print("Re-checking availability...")
        new_slots = booking_service.get_availability(device_id, today)
        found = any(s['start'] == target_slot['start'] for s in new_slots)
        if not found:
            print("SUCCESS: Slot is correctly marked as booked.")
        else:
            print("FAILURE: Slot is still available.")
    else:
        print("Skipping booking test (no slots).")

if __name__ == "__main__":
    run_tests()
