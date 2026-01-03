import os
import json
import requests
from datetime import datetime, timedelta
from services import booking_service

SYSTEM_PROMPT = """
You are a Flight Simulator Booking Assistant. 
Your goal is to help users list simulators, check availability, and book sessions.

You must maintain context from the "Conversation History". If a user says "the second one" or "that simulator", refer to the previous list or context to identify the specific device.

You have access to the following TOOLS. You must strictly output JSON to call a tool or reply to the user.
Do not output markdown code blocks. Just the JSON object.

TOOLS:
1. `list_devices`: Parameters: `campus_id` (optional int), `campus_name` (optional str), `device_code` (optional str)
2. `check_availability`: Parameters: `device_id` (optional int), `device_code` (optional str), `date` (str, YYYY-MM-DD). Use today's date if relative.
   - You MUST provide either `device_id` or `device_code`.
3. `add_to_cart`: Parameters: `device_id` (optional int), `device_code` (optional str), `start_time` (str, HH:MM or ISO), `date` (optional str).
   - USE THIS TOOL when the user says "book", "add", "reserve" or selects a time.
   - You can infer missing `device_id` or `date` from the `Last Interaction Context`.
   - `end_time` is auto-calculated (4 hours), so you don't need to provide it.
4. `view_cart`: No parameters.
5. `confirm_booking`: No parameters.
6. `reply`: Parameters: `message` (str). Use this to ask clarifying questions or provide info.

RESPONSE FORMAT:
{{
    "action": "one_of_the_tool_names_or_reply",
    "params": {{ ... }}
}}



CONTEXT:
Today is: {today}
Current Session Cart: {cart}
Last Interaction Context: {context}

Conversation History:
{chat_history}

User Input: {user_input}
"""

def process_message(message: str, session) -> str:
    """
    Process message using LLM via direct HTTP request if configured, otherwise fallback to mock logic.
    """
    if 'llm_context' not in session:
        session['llm_context'] = {}
        
    if 'chat_history' not in session:
        session['chat_history'] = []
        
    api_key = os.getenv('OPENAI_API_KEY')
    response_text = ""
    
    if api_key and api_key != 'YOUR_KEY_HERE':
        response_text = run_llm_agent(message, session)
    else:
        response_text = run_mock_agent(message, session)
        
    # Append to history
    session['chat_history'].append({"role": "user", "content": message})
    session['chat_history'].append({"role": "assistant", "content": response_text})
    
    # Keep last 20 messages (10 rounds)
    if len(session['chat_history']) > 20:
        session['chat_history'] = session['chat_history'][-20:]
        
    session.modified = True
    
    return response_text

def run_llm_agent(message: str, session) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    cart_summary = json.dumps(session.get('cart', []))
    context = session.get('llm_context', {})
    
    # Format History
    history_list = session.get('chat_history', [])
    history_str = ""
    for msg in history_list:
        role = "User" if msg['role'] == "user" else "Assistant"
        # Truncate long content in history to save tokens
        content = msg['content']
        if len(content) > 500: content = content[:500] + "..."
        history_str += f"{role}: {content}\n"
    
    prompt = SYSTEM_PROMPT.format(
        today=today,
        cart=cart_summary,
        context=json.dumps(context),
        chat_history=history_str,
        user_input=message
    )
    
    # Load Env Vars
    base_url = (os.getenv('OPENAI_API_BASE') or '').strip().strip('"').strip("'")
    api_key = (os.getenv('OPENAI_API_KEY') or '').strip().strip('"').strip("'")
    deployment = os.getenv('AZURE_DEPLOYMENT_NAME', 'gpt-4o')
    api_version = os.getenv('OPENAI_API_VERSION', '2024-02-15-preview')
    
    # Construct URL for Azure
    # https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions?api-version={version}
    # Handle if user put full path or just base
    if '/chat/completions' not in base_url:
        url = f"{base_url}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    else:
        url = base_url # Assume full URL provided if it looks like one

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Output JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        # Naive JSON cleaning
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "")
        content = content.strip()
        
        tool_data = json.loads(content)
        return execute_tool(tool_data, session)
        
    except Exception as e:
        debug_info = f"Error: {str(e)[:200]} | URL={url}"
        print(f"LLM Request Failed: {debug_info}")
        return run_mock_agent(message, session, error=debug_info)

def execute_tool(data: dict, session) -> str:
    action = data.get('action')
    params = data.get('params', {})
    
    if action == 'list_devices':
        c_name = params.get('campus_name', '').lower()
        c_id = params.get('campus_id')
        if not c_id and c_name:
            if 'miami' in c_name: c_id = 1
            elif 'gatwick' in c_name: c_id = 2
            elif 'singapore' in c_name: c_id = 3
        
        devices = booking_service.get_devices(campus_id=c_id, device_code=params.get('device_code'))
        resp = "Found devices:\n"
        for d in devices:
            resp += f"- {d['DeviceName']} ({d['DeviceCode']}) at {d['CampusName']}\n"
        return resp

    elif action == 'check_availability':
        d_id = params.get('device_id')
        d_code = params.get('device_code')
        date = params.get('date')
        
        if not d_id and not d_code:
            return "I need a Device ID or Code (e.g., B737-8-MIA-#1) to check availability."
            
        # Resolve ID if only code provided
        if not d_id and d_code:
            devs = booking_service.get_devices(device_code=d_code)
            if not devs:
                return f"I couldn't find a device with code '{d_code}'."
            # Pick the first one (assume exact or best match)
            d_id = devs[0]['DeviceId']
            # Optional: Notify user if multiple found? For now assume specific.
        
        if not date:
            return "I need a Date to check availability."
            
        slots = booking_service.get_availability(d_id, date)
        if not slots:
            # Resolve name for better error message
            dev_name = f"Device {d_id}"
            devs = booking_service.get_devices(campus_id=None) # Get all to find match, or optimized lookup
            # Since get_devices filters, let's just get by ID if we could, but our service currently filters by campus/code.
            # Let's simple iterate or filter.
            # Actually booking_service.get_devices implementation:
            # def get_devices(campus_id=None, device_code=None)
            # It doesn't support by ID directly in signature shown before? 
            # Wait, I can just filter the full list or add id support to service.
            # Let's rely on what we have:
            found = [d for d in booking_service.get_devices() if d['DeviceId'] == int(d_id)]
            if found:
                dev_name = f"{found[0]['DeviceName']} ({found[0]['DeviceCode']})"
            
            return f"No availability on {date} for {dev_name}."
        
        # SAVE CONTEXT
        session['llm_context']['last_device_id'] = d_id
        session['llm_context']['last_device_code'] = d_code
        session['llm_context']['last_date'] = date
        session.modified = True
        
        resp = f"Available slots on {date}:\n"
        for s in slots:
            resp += f"- {s['label']}\n"
        return resp

    elif action == 'add_to_cart':
        # Resolve Params from Context if missing
        context = session.get('llm_context', {})
        d_id = params.get('device_id') or context.get('last_device_id')
        d_code = params.get('device_code') or params.get('device_name') # sometimes LLM puts code in name
        date = params.get('date') or context.get('last_date')
        start_time = params.get('start_time')
        
        # Resolve Device ID from Code if needed
        if not d_id and d_code:
            # Try to resolve code 
            # Note: Context might have code but we prefer ID. 
            # If we only have code from param:
            devs = booking_service.get_devices(device_code=d_code)
            if devs: d_id = devs[0]['DeviceId']
            
        if not d_id:
             return "I need to know which device you want to book. Please specify or check availability first."
             
        if not date:
             return "I need to know the date for the booking."
             
        if not start_time:
             return "Please specify the start time (e.g. '17:00')."
             
        # Normalize Start Time / End Time
        # User might say "17:00", we need ISO format for backend? 
        # Backend mocks usually take generic strings but let's be robust.
        # Construct full ISO strings if only HH:MM provided
        try:
            # Check if start_time is just time
            if 'T' not in start_time and len(start_time) <= 5: 
                start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            else:
                # Assume ISO or strict format
                start_dt = datetime.fromisoformat(start_time)
        except:
             # Fallback try
             try:
                 start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
             except:
                 return f"Could not understand time format: {start_time}"

        # Auto-calc end time (4 hours)
        end_dt = start_dt + timedelta(hours=4) # Fixed 4h duration
        
        # Helper to get name
        dev_name_for_cart = params.get('device_name')
        if not dev_name_for_cart:
            # Try context
            dev_name_for_cart = context.get('last_device_code')
            # If still not good or we want full name, lookup
            found = [d for d in booking_service.get_devices() if d['DeviceId'] == int(d_id)]
            if found:
                dev_name_for_cart = f"{found[0]['DeviceName']} ({found[0]['DeviceCode']})"
            else:
                dev_name_for_cart = f"Device {d_id}"

        cart_item = {
            "DeviceId": d_id,
            "DeviceName": dev_name_for_cart,
            "SlotStart": start_dt.isoformat(),
            "SlotEnd": end_dt.isoformat(),
            "Label": f"{start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}",
            "Date": date
        }
        session['cart'].append(cart_item)
        return f"Added slot {cart_item['Label']} for {dev_name_for_cart} to cart!"

    elif action == 'view_cart':
        cart = session.get('cart', [])
        if not cart: return "Cart is empty."
        return "Cart contents:\n" + "\n".join([f"{i['DeviceName']} at {i['Label']}" for i in cart])

    elif action == 'confirm_booking':
        cart = session.get('cart', [])
        if not cart: return "Cart is empty."
        res = booking_service.book_sessions(cart)
        session['cart'] = []
        return f"Booked! Conf: {res['confirmation_number']}"

    elif action == 'reply':
        return params.get('message', "I'm not sure.")
        
    else:
        return "I didn't understand that action."

def run_mock_agent(message: str, session, error: str = None) -> str:
    """
    Fallback regex agent.
    """
    prefix = ""
    if error:
        prefix = f"[DEBUG: LLM Failed: {error}]\n"

    message = message.lower()
    if "list" in message or "show" in message or "devices" in message:
        c_id = 1 if "miami" in message else (2 if "gatwick" in message else (3 if "singapore" in message else None))
        devs = booking_service.get_devices(campus_id=c_id)
        return prefix + "\n".join([f"{d['DeviceName']} ({d['DeviceCode']})" for d in devs])
        
    if "available" in message:
        return prefix + "To check availability with the basic agent, I need a specific flow. (Please configure LLM for better experience)"
        
    return prefix + "LLM Key not configured. Using basic fallback. I can list devices."
