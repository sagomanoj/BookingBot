from flask import Flask, request, jsonify, session, send_from_directory
from flask_session import Session
import os
from dotenv import load_dotenv
from services import booking_manager, chat_agent

load_dotenv()

app = Flask(__name__, static_folder='static')

# Session Config
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "simulation_secret_key"
Session(app)

@app.route('/')
def home():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# --- Mock APIs ---

@app.route('/api/devices', methods=['GET'])
def list_devices():
    campus_id = request.args.get('campus_id', type=int)
    device_code = request.args.get('device_code')
    devices = booking_manager.get_devices(campus_id, device_code)
    return jsonify(devices)

@app.route('/api/booked_sessions', methods=['GET']) # Using GET mostly, but payload usually POST for list of IDs. Let's use POST for complex filter
def list_booked_sessions():
    """
    Expects JSON:
    {
        "device_ids": [101, 102],
        "start_date": "ISO_STRING",
        "end_date": "ISO_STRING"
    }
    """
    # For GET requests with simpler queries:
    if request.method == 'GET':
        # simplistic fallback or error
        return jsonify({"error": "Use POST with device_ids list"}), 400

@app.route('/api/booked_sessions', methods=['POST'])
def get_booked_sessions_api():
    data = request.json
    device_ids = data.get('device_ids', [])
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not device_ids or not start_date or not end_date:
        return jsonify({"error": "Missing parameters"}), 400
        
    sessions = booking_manager.get_booked_sessions(device_ids, start_date, end_date)
    return jsonify(sessions)

@app.route('/api/availability', methods=['GET'])
def check_availability():
    device_id = request.args.get('device_id', type=int)
    date = request.args.get('date') # YYYY-MM-DD or ISO
    
    if not device_id or not date:
        return jsonify({"error": "Missing params"}), 400
        
    slots = booking_manager.get_availability(device_id, date)
    return jsonify(slots)

@app.route('/api/book', methods=['POST'])
def book_session():
    # In a real app, cart would be passed or retrieved from session
    # Here we expect the agent to pass the cart items to confirm
    data = request.json
    cart = data.get('cart', [])
    
    if not cart:
        # Fallback to session cart if implemented there
        cart = session.get('cart', [])
        
    if not cart:
         return jsonify({"error": "Cart is empty"}), 400
         
    result = booking_manager.book_sessions(cart)
    
    # Clear session cart
    session['cart'] = []
    
    return jsonify(result)

# --- Chat API ---

@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    
    # Initialize session cart if needed
    if 'cart' not in session:
        session['cart'] = []
    
    # Call the agent
    response_text = chat_agent.process_message(user_message, session)
    
    return jsonify({"response": response_text})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
