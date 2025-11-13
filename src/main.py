from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from src.database import init_db, get_connection
app = FastAPI()

# ------------------------------ MODELS ------------------------------

class StudentCreate(BaseModel):
    name: str

class RecognitionRequest(BaseModel):
    sender_id: int
    recipient_id: int
    credits: int

class EndorseRequest(BaseModel):
    recognition_id: int
    endorser_id: int

class RedemptionRequest(BaseModel):
    student_id: int
    credits: int


# ------------------------------ STARTUP ------------------------------

@app.on_event("startup")
def startup():
    init_db()


# ------------------------------ STUDENTS ------------------------------

@app.post("/students")
def create_student(student: StudentCreate):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO students (name, balance, monthly_sent) VALUES (?, ?, ?)",
                   (student.name, 100, 0))
    conn.commit()

    student_id = cursor.lastrowid
    conn.close()
    return {"id": student_id, "name": student.name, "balance": 100, "monthly_sent": 0}


@app.get("/students")
def get_all_students():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]


@app.get("/students/{student_id}")
def get_student(student_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id=?", (student_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Student not found")

    return dict(row)


# ------------------------------ RECOGNITION ------------------------------

@app.post("/recognize")
def recognize(request: RecognitionRequest):
    if request.sender_id == request.recipient_id:
        raise HTTPException(status_code=400, detail="Cannot recognize yourself")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id=?", (request.sender_id,))
    sender = cursor.fetchone()

    cursor.execute("SELECT * FROM students WHERE id=?", (request.recipient_id,))
    recipient = cursor.fetchone()

    if not sender or not recipient:
        raise HTTPException(status_code=404, detail="Sender or recipient not found")

    sender = dict(sender)
    recipient = dict(recipient)

    if request.credits > sender["balance"]:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    if sender["monthly_sent"] + request.credits > 100:
        raise HTTPException(status_code=400, detail="Monthly sending limit exceeded")

    new_sender_balance = sender["balance"] - request.credits
    new_recipient_balance = recipient["balance"] + request.credits
    new_sender_monthly = sender["monthly_sent"] + request.credits

    cursor.execute("UPDATE students SET balance=?, monthly_sent=? WHERE id=?",
                   (new_sender_balance, new_sender_monthly, request.sender_id))

    cursor.execute("UPDATE students SET balance=? WHERE id=?",
                   (new_recipient_balance, request.recipient_id))

    timestamp = datetime.utcnow().isoformat()
    cursor.execute(
        "INSERT INTO recognitions (sender_id, recipient_id, credits, timestamp) VALUES (?, ?, ?, ?)",
        (request.sender_id, request.recipient_id, request.credits, timestamp)
    )

    recognition_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "recognition_id": recognition_id,
        "sender_id": request.sender_id,
        "recipient_id": request.recipient_id,
        "credits": request.credits,
        "timestamp": timestamp
    }


# ------------------------------ ENDORSEMENT ------------------------------

@app.post("/endorse")
def endorse(request: EndorseRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM recognitions WHERE id=?", (request.recognition_id,))
    rec = cursor.fetchone()

    if not rec:
        raise HTTPException(status_code=404, detail="Recognition not found")

    try:
        cursor.execute(
            "INSERT INTO endorsements (recognition_id, endorser_id) VALUES (?, ?)",
            (request.recognition_id, request.endorser_id),
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Endorser has already endorsed this recognition")

    conn.commit()
    conn.close()

    return {"message": "Endorsed", "recognition_id": request.recognition_id, "endorser_id": request.endorser_id}


# ------------------------------ REDEMPTION ------------------------------

@app.post("/redeem")
def redeem(request: RedemptionRequest):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE id=?", (request.student_id,))
    student = cursor.fetchone()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student = dict(student)

    if request.credits > student["balance"]:
        raise HTTPException(status_code=400, detail="Insufficient credits to redeem")

    new_balance = student["balance"] - request.credits
    cursor.execute("UPDATE students SET balance=? WHERE id=?", (new_balance, request.student_id))

    voucher_value = request.credits * 5
    timestamp = datetime.utcnow().isoformat()

    cursor.execute(
        "INSERT INTO redemptions (student_id, credits, voucher_value, timestamp) VALUES (?, ?, ?, ?)",
        (request.student_id, request.credits, voucher_value, timestamp),
    )

    conn.commit()
    conn.close()

    return {
        "student_id": request.student_id,
        "redeemed_credits": request.credits,
        "voucher_value_inr": voucher_value,
        "timestamp": timestamp
    }


# ------------------------------ LEADERBOARD ------------------------------

@app.get("/leaderboard")
def leaderboard(limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            s.id AS student_id,
            s.name,
            COALESCE(SUM(r.credits), 0) AS total_credits_received,
            COUNT(r.id) AS recognition_count,
            (
                SELECT COUNT(*)
                FROM recognitions rr
                JOIN endorsements e ON rr.id = e.recognition_id
                WHERE rr.recipient_id = s.id
            ) AS endorsements_total
        FROM students s
        LEFT JOIN recognitions r ON s.id = r.recipient_id
        GROUP BY s.id
        ORDER BY total_credits_received DESC, student_id ASC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ------------------------------ MONTHLY RESET ------------------------------

@app.post("/admin/reset_month")
def reset_month(carry_forward: bool = Query(default=False)):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    rows = cursor.fetchall()

    for row in rows:
        row = dict(row)

        carry = min(row["balance"], 50) if carry_forward else 0
        new_balance = 100 + carry

        cursor.execute(
            "UPDATE students SET balance=?, monthly_sent=? WHERE id=?",
            (new_balance, 0, row["id"])
        )

    conn.commit()
    conn.close()

    return {
        "message": "Monthly reset completed",
        "carry_forward_applied": carry_forward,
        "timestamp": datetime.utcnow().isoformat()
    }
