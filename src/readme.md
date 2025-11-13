# Boostly — Student Recognition Platform

Built with **FastAPI** and **SQLite**

Boostly is a lightweight platform that enables students to recognize peers, endorse recognitions, and redeem earned credits. The application strictly follows all the business rules provided in the problem statement and includes optional step-up features such as monthly resets and leaderboard rankings.

---

## 1. Setup Instructions

### 1.1 Create a Virtual Environment

python -m venv venv
venv\Scripts\Activate

### 1.2 Install Dependencies

pip install -r requirements.txt

### 1.3 Database Setup

No manual setup required.
The SQLite database (`data.db`) is auto-created on startup.

---

## 2. Running the Application

Start the server: uvicorn src.main:app --reload

Application URL: http://127.0.0.1:8000

---

## 3. Project Structure

your-repository/
├── src/
│ ├── init.py
│ ├── main.py
│ ├── database.py
│ └── readme.md
├── requirements.txt
├── prompt/
│ └── llm-chat-export.txt
└── test-cases/
└── test-cases.txt

---

## 4. Business Rules

### Recognition

- Each student starts each month with **100 credits**.
- Students cannot recognize themselves.
- Students cannot send more credits than their current balance.
- Students cannot exceed the monthly sending limit of **100 credits**.
- Sending credits reduces sender balance and increases recipient balance.

### Endorsements

- A student can endorse the same recognition **only once**.
- Endorsements do not affect balances.
- `(recognition_id, endorser_id)` is unique.

### Redemption

- Students can redeem only credits they have **received**.
- Credits are permanently deducted.
- Conversion rate: **₹5 per credit**.

### Monthly Reset (Step-Up)

- Monthly send limit resets to 0.
- Base credits reset to 100.
- Up to **50 credits** may be carried forward from previous balance.

### Leaderboard (Step-Up)

- Ranked by total credits received (desc).
- Tie-breaker: student_id ascending.
- Displays:
  - total credits received
  - total recognitions received
  - total endorsements received

---

## 5. API Endpoints

### 5.1 Student Management

#### Create Student

**POST /students**

{
"name": "alice"
}

#### List All Students

GET /students

#### Get Student by ID

GET /students/{student_id}

---

### 5.2 Recognition

#### Send Recognition

POST /recognize
{
"sender_id": 1,
"recipient_id": 2,
"credits": 20
}

---

### 5.3 Endorsements

#### Endorse Recognition

POST /endorse
{
"recognition_id": 1,
"endorser_id": 3
}

Duplicate endorsement returns:
{
"detail": "Endorser has already endorsed this recognition"
}

---

### 5.4 Redemption

#### Redeem Credits

POST /redeem
{
"student_id": 2,
"credits": 10
}

Sample response:
{
"student_id": 2,
"redeemed_credits": 10,
"voucher_value_inr": 50,
"timestamp": "2025-01-01T10:00:00Z"
}

---

### 5.5 Leaderboard

#### Get Leaderboard

GET /leaderboard?limit=10

---

### 5.6 Monthly Reset

#### Reset Monthly Credits

POST /admin/reset_month?carry_forward=true

---

## 6. Quick Testing Guide

### Create students

POST /students {"name":"alice"}
POST /students {"name":"bob"}

### Alice recognizes Bob

POST /recognize {"sender_id":1,"recipient_id":2,"credits":20}

### Check Bob's updated balance

GET /students/2

### Endorse the recognition

(assuming recognition_id = 1)

POST /endorse {"recognition_id":1,"endorser_id":3}

### Redeem credits

POST /redeem {"student_id":2,"credits":10}

### Run monthly reset

POST /admin/reset_month?carry_forward=true

### View leaderboard

GET /leaderboard?limit=5

---

## 7. Security Considerations

- **Input validation** handled by FastAPI + Pydantic.
- **Duplicate endorsements** prevented via DB UNIQUE constraint.
- **Business rule enforcement** at API layer.
- **Admin endpoint** isolated under `/admin`.
- **All activities** logged in SQLite tables for traceability.
- **No unauthorized credit changes**: all balance updates validated.

---

## 8. Submission Checklist

- [x] `src/main.py` implemented
- [x] `src/database.py` implemented
- [x] `src/readme.md` (this file) updated
- [x] `requirements.txt` contains compatible versions
- [x] `prompt/llm-chat-export.txt` updated
- [x] `test-cases/test-cases.txt` completed
- [x] Repo pushed publicly with correct name format
- [x] Application runs via: uvicorn src.main:app --reload

---

## End of Documentation
