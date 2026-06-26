from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.database_mysql import get_db
from app.models_mysql import StudentModel, ClassModel, TeacherModel, SubjectModel, AttendanceModel
from app.supabase_client import sync_to_supabase_auth, supabase
from pydantic import BaseModel

router = APIRouter()

# --- VALIDATION SCHEMAS ---
class StudentCreate(BaseModel):
    name: str
    email: str
    class_id: int

class ClassCreate(BaseModel):
    name: str
    stream: str

class TeacherCreate(BaseModel):
    name: str
    email: str
    specialization: str

class AttendanceCreate(BaseModel):
    student_id: int
    date_log: date
    status: str

class PaymentCreate(BaseModel):
    student_id: int
    amount: float
    status: str

# --- CLASS ENDPOINTS ---
@router.post("/classes", tags=["Academic Classes"])
def create_class(item: ClassCreate, db: Session = Depends(get_db)):
    new_class = ClassModel(name=item.name, stream=item.stream)
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    return {"message": "Class created locally", "id": new_class.id}

@router.get("/classes", tags=["Academic Classes"])
def get_classes(db: Session = Depends(get_db)):
    return db.query(ClassModel).all()

# --- STUDENT CRUD ENDPOINTS ---
@router.post("/students", tags=["Student Management"])
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    try:
        new_student = StudentModel(name=student.name, email=student.email, class_id=student.class_id)
        db.add(new_student)
        db.commit()
        db.refresh(new_student)
        sync_to_supabase_auth(new_student.email) # Identity cloud trigger
        return {"status": "Success", "student_id": new_student.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/students", tags=["Student Management"])
def list_students(db: Session = Depends(get_db)):
    return db.query(StudentModel).all()

@router.delete("/students/{student_id}", tags=["Student Management"])
def delete_student(student_id: int, db: Session = Depends(get_db)):
    target = db.query(StudentModel).filter(StudentModel.id == student_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(target)
    db.commit()
    return {"message": f"Student {student_id} removed completely"}

# --- TEACHER ENDPOINTS ---
@router.post("/teachers", tags=["Faculty Management"])
def register_teacher(faculty: TeacherCreate, db: Session = Depends(get_db)):
    try:
        new_teacher = TeacherModel(name=faculty.name, email=faculty.email, specialization=faculty.specialization)
        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher)
        sync_to_supabase_auth(new_teacher.email) # Identity cloud trigger
        return {"message": "Faculty registered", "id": new_teacher.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# --- ATTENDANCE ENDPOINTS ---
@router.post("/attendance", tags=["Attendance Records"])
def log_attendance(record: AttendanceCreate, db: Session = Depends(get_db)):
    new_log = AttendanceModel(student_id=record.student_id, date=record.date_log, status=record.status)
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return {"message": "Attendance state recorded successfully"}

# --- WORKFLOW TRIGGER 2: DIRECT CLOUD FINANCIAL DATA STREAMING ---
@router.post("/payments", tags=["Cloud Financial Service"])
def submit_payment_ledger(payment: PaymentCreate):
    """
    Bypasses the local database completely to stream transactional records 
    directly up to the secure Cloud Supabase PostgreSQL framework database.
    """
    try:
        transaction_record = {
            "student_id": payment.student_id,
            "amount": payment.amount,
            "date": str(date.today()),
            "status": payment.status
        }
        response = supabase.table("payment").insert(transaction_record).execute()
        return {"status": "Transaction stream verified", "cloud_data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloud data delivery failure: {str(e)}")