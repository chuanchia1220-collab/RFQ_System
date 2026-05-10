import os
import logging
from flask import Flask, render_template, request, jsonify
import database as db
from ai_agent import ask_procurement_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("system.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)

# Initialize DB on load
db.init_db()
db.seed_dummy_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/suppliers', methods=['GET'])
def get_suppliers():
    """Returns the flat list of all document statuses."""
    try:
        data = db.get_all_document_statuses()
        return jsonify(data)
    except Exception as e:
        logging.error("Error fetching suppliers data", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Receives chat message and returns AI response."""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "No message provided"}), 400

        user_message = data['message']
        logging.info(f"Received chat message: {user_message}")

        # Call the AI Agent (REST API version)
        response_text = ask_procurement_agent(user_message)

        return jsonify({"response": response_text})

    except Exception as e:
        logging.error("Error processing chat message", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the Flask app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)