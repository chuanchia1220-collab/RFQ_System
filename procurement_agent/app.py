import os
import logging
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
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

app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handles document upload, renaming, and database update."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        supplier_id = request.form.get('supplier_id')
        doc_type = request.form.get('doc_type')

        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        if not supplier_id or not doc_type:
            return jsonify({"error": "Missing supplier_id or doc_type"}), 400

        if file:
            # Extract extension
            original_filename = secure_filename(file.filename)
            ext = os.path.splitext(original_filename)[1]

            # Sanitize inputs to prevent path traversal
            safe_supplier_id = secure_filename(supplier_id)
            safe_doc_type = secure_filename(doc_type)

            # Construct normalized filename
            new_filename = f"{safe_supplier_id}_{safe_doc_type}{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

            # Save file
            file.save(file_path)

            # Update database status to '已簽回'
            db.update_document_status(supplier_id, doc_type, file_path, status='已簽回')

            logging.info(f"Successfully uploaded and renamed file to {new_filename} for Supplier {supplier_id}")
            return jsonify({"message": "File uploaded successfully", "filename": new_filename})

    except Exception as e:
        logging.error("Error handling file upload", exc_info=True)
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