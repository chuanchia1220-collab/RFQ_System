import streamlit as st
import os
import time
import logging
from datetime import datetime
import database as db
from llm_agent import ask_procurement_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("system.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# OpenClaw Terminal CSS Styles (Dark mode, Monospace)
st.set_page_config(page_title="Next-Gen Procurement Agent", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    /* Global Terminal Style */
    body {
        background-color: #0d1117;
        color: #00ff00;
        font-family: 'Courier New', Courier, monospace;
    }

    .stApp {
        background-color: #0d1117;
    }

    /* Headers and Text */
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #00ff00 !important;
        font-family: 'Courier New', Courier, monospace !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }

    /* Buttons */
    .stButton>button {
        background-color: #21262d;
        color: #00ff00;
        border: 1px solid #30363d;
        border-radius: 4px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #30363d;
        border-color: #8b949e;
    }

    /* Dataframes/Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid #30363d;
    }

    /* Input fields */
    .stTextInput>div>div>input {
        background-color: #0d1117;
        color: #00ff00;
        border: 1px solid #30363d;
    }
</style>
""", unsafe_allow_html=True)


# Initialize DB on load
@st.cache_resource
def initialize_system():
    db.init_db()
    db.seed_dummy_data()
    return True

initialize_system()

# --- Helper function for Email Automation ---
def generate_eml_drafts(selected_supplier_ids):
    """
    Generates .eml drafts for the selected suppliers with missing documents.
    Implements physical rate-limiting, error abort threshold, and resume capability.
    """
    PROCESSED_LOG = "processed_mails.log"
    OUTPUT_DIR = "eml_drafts"

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Read already processed IDs to support resume
    processed_ids = set()
    if os.path.exists(PROCESSED_LOG):
        with open(PROCESSED_LOG, "r") as f:
            processed_ids = set([line.strip() for line in f.readlines()])

    missing_docs_data = db.get_missing_documents_by_supplier(selected_supplier_ids)

    # Group by supplier
    suppliers_to_process = {}
    for row in missing_docs_data:
        sid = row['Supplier_ID']
        if sid in processed_ids:
            continue

        if sid not in suppliers_to_process:
            suppliers_to_process[sid] = {
                'Name': row['Name'],
                'Email': row['Email'],
                'Docs': []
            }
        suppliers_to_process[sid]['Docs'].append(row['Doc_Type'])

    if not suppliers_to_process:
        return "No new drafts to generate. All selected items might have been processed already."

    error_count = 0
    generated_count = 0
    progress_bar = st.progress(0)
    status_text = st.empty()

    total = len(suppliers_to_process)

    for idx, (sid, data) in enumerate(suppliers_to_process.items()):
        if error_count >= 6:
            logging.error("Aborting batch email generation due to 6 consecutive errors.")
            return f"Aborted after {generated_count} generations due to excessive errors."

        status_text.text(f"Processing {sid} ({data['Name']})...")

        try:
            # Generate EML content
            date_str = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0800")
            docs_str = ", ".join(data['Docs'])

            eml_content = f"""Date: {date_str}
From: procurement_agent@local.system
To: {data['Email']}
Subject: Action Required: Missing Compliance Documents for {data['Name']}

Dear {data['Name']},

Our records indicate that we are still waiting for the following compliance documents from your side:
{docs_str}

Please sign and return them as soon as possible.

Best regards,
Next-Gen Procurement Agent
"""
            filename = os.path.join(OUTPUT_DIR, f"{sid}_{datetime.now().strftime('%Y%m%d%H%M%S')}.eml")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(eml_content)

            # Log success
            with open(PROCESSED_LOG, "a") as f:
                f.write(f"{sid}\n")

            generated_count += 1
            error_count = 0  # Reset on success to ensure consecutive logic
            logging.info(f"Generated EML for {sid}")

            # Physical rate limiting (12 seconds)
            if idx < total - 1:
                 status_text.text(f"Waiting 12s to prevent rate limiting...")
                 time.sleep(12)

        except Exception as e:
            error_count += 1
            logging.error(f"Error generating EML for {sid}", exc_info=True)

        # Update progress
        progress_bar.progress((idx + 1) / total)

    status_text.text("Batch generation complete.")
    return f"Successfully generated {generated_count} .eml draft(s)."


# --- UI Layout ---

st.title("> Next-Gen Procurement Agent_")

# Sidebar
st.sidebar.header("System Controls")
all_suppliers = db.get_suppliers()
supplier_options = [s['Supplier_ID'] for s in all_suppliers]

st.sidebar.subheader("Batch Operations")
selected_suppliers = st.sidebar.multiselect("Select Suppliers for Email Batch:", options=supplier_options)

if st.sidebar.button("Generate .eml Drafts"):
    if selected_suppliers:
        with st.spinner("Executing batch generation..."):
            result_msg = generate_eml_drafts(selected_suppliers)
            st.sidebar.success(result_msg)
    else:
        st.sidebar.warning("Please select at least one supplier.")


# Main Content Tabs
tab1, tab2 = st.tabs(["[ Compliance Dashboard ]", "[ AI Agent Chat ]"])

with tab1:
    st.header(">> Compliance Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Search by Supplier")
        search_sid = st.selectbox("Select Supplier ID", options=[""] + supplier_options)
        if search_sid:
            docs = db.get_documents_by_supplier(search_sid)
            if docs:
                st.dataframe(docs, use_container_width=True)
            else:
                st.write("No documents found.")

    with col2:
        st.subheader("Missing Documents Overview")
        if st.button("Refresh Overview"):
            missing = db.get_missing_documents()
            if missing:
                st.dataframe(missing, use_container_width=True)
            else:
                st.write("All suppliers are compliant.")
        else:
            missing = db.get_missing_documents()
            if missing:
                st.dataframe(missing, use_container_width=True)

with tab2:
    st.header(">> AI Agent Chat")
    st.write("Ask natural language questions about supplier compliance.")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ex: 幫我查出目前有哪幾家供應商還沒簽回 NDA？"):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Agent is querying the database..."):
            response = ask_procurement_agent(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            st.markdown(response)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
