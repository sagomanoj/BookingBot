# BookingBot

A Flight Simulator Booking Assistant chatbot built with Flask and OpenAI.

## Prerequisites

- Python 3.8+
- An OpenAI or Azure OpenAI API key

## Setup Instructions

Follow these steps to set up and run the application on your local machine.

### 1. Clone the Repository
```bash
git clone https://github.com/sagomanoj/BookingBot.git
cd BookingBot
```

### 2. Create a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies.

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
Once the virtual environment is activated, install the required packages:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the template environment file and fill in your API keys:
```bash
cp .env.example .env
```
Open the newly created `.env` file and enter your `OPENAI_API_KEY` and other configurations.

### 5. Run the Application
Start the Flask development server:
```bash
python app.py
```
The application will be available at `http://127.0.0.1:5000`.

## Testing
You can run the `verify_logic.py` script to test the core booking services:
```bash
python verify_logic.py
```
