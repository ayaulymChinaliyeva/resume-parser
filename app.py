import streamlit as st
import requests
import pandas as pd
import sqlite3

# 🟢 API Key for hh.ru
HH_API_TOKEN = "your_hh_api_token"

# 🟢 Database Setup (Runs on Streamlit Cloud)
DB_FILE = "candidates.db"

def create_database():
    """Create SQLite database with candidates table if not exists."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            experience INTEGER,
            status TEXT,
            salary TEXT
        )
    """)
    conn.commit()
    conn.close()

# 🟢 Fetch Resumes from hh.ru
def fetch_hh_resumes(query):
    url = "https://api.hh.ru/resumes"
    headers = {"User-Agent": "ResumeParserApp/1.0", "Authorization": f"Bearer {HH_API_TOKEN}"}
    params = {"text": query, "per_page": 10}
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("items", []) if response.status_code == 200 else []

# 🟢 Save Resumes to Database
def save_to_database(candidates):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for candidate in candidates:
        cursor.execute("""
            INSERT INTO candidates (name, email, experience, status, salary)
            VALUES (?, ?, ?, ?, ?)
        """, (candidate["name"], candidate["email"], candidate["experience"], "New", candidate["salary"]))
    conn.commit()
    conn.close()

# 🟢 Load Data from Database
def load_from_database():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql("SELECT * FROM candidates", conn)
    conn.close()
    return df

# 🟢 Update Candidate Status
def update_candidate_status(candidate_id, new_status):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE candidates SET status = ? WHERE id = ?", (new_status, candidate_id))
    conn.commit()
    conn.close()

# 🟢 Streamlit UI
def main():
    st.title("📄 Resume Management System")

    # Initialize database
    create_database()

    # Sidebar Inputs
    st.sidebar.header("Search Criteria")
    search_text = st.sidebar.text_input("Job Title", value="Python Developer")
    
    # Fetch Resumes
    if st.sidebar.button("Fetch Resumes"):
        hh_resumes = fetch_hh_resumes(search_text)
        candidates = [{"name": res.get("first_name", "Unknown"), "email": res.get("email", "N/A"), "experience": res.get("experience", {}).get("months", 0) // 12, "salary": res.get("salary", {}).get("amount", "N/A")} for res in hh_resumes]
        save_to_database(candidates)
        st.success(f"✅ {len(candidates)} resumes saved!")

    # Load Candidates
    df = load_from_database()
    st.subheader("📋 Candidates")
    
    if not df.empty:
        for i, row in df.iterrows():
            col1, col2, col3 = st.columns([3, 2, 2])
            col1.write(f"👤 {row['name']} - {row['experience']} years experience")
            new_status = col2.selectbox(
                "Update Status",
                ["New", "Shortlisted", "Rejected", "Interview"],
                index=["New", "Shortlisted", "Rejected", "Interview"].index(row["status"]),
                key=row["id"]
            )
            if col3.button("✔ Save", key=f"save_{row['id']}"):
                update_candidate_status(row["id"], new_status)
                st.experimental_rerun()

    # Export Button
    if st.button("📤 Export to Excel"):
        df.to_excel("candidates.xlsx", index=False)
        st.success("✅ Exported!")

if __name__ == "__main__":
    main()
