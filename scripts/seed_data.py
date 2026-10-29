import os
import sys
import random
from datetime import datetime, timedelta

# Ensure backend app is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.db.session import get_db
from backend.app.db.init_db import init_database
from backend.app.core.config import settings
from backend.app.core.logging import logger

DEPARTMENTS = ["Cardiology", "Endocrinology", "Family Medicine", "Pediatrics", "Urgent Care"]
PROVIDERS = {
    "Cardiology": ["Dr. Elena Rostova, MD", "Dr. Marcus Vance, MD"],
    "Endocrinology": ["Dr. Sarah Chen, MD", "Dr. David Miller, MD"],
    "Family Medicine": ["Dr. James Wilson, MD", "Dr. Aisha Patel, MD"],
    "Pediatrics": ["Dr. Carlos Gomez, MD", "Dr. Emily Taylor, MD"],
    "Urgent Care": ["Dr. Kevin Brooks, MD", "Dr. Rachel Green, DO"]
}

FIRST_NAMES = [
    "Alexander", "Beatriz", "Charles", "Diana", "Ethan", "Fatima", "George", "Hannah",
    "Isaac", "Julia", "Kenneth", "Leila", "Mateo", "Nora", "Oliver", "Penelope",
    "Quinn", "Rafael", "Sophia", "Thomas", "Uma", "Victor", "Wendy", "Xavier", "Yasmine", "Zachary",
    "Liam", "Emma", "Noah", "Olivia", "William", "Ava", "James", "Isabella", "Benjamin", "Mia",
    "Elijah", "Charlotte", "Lucas", "Amelia", "Mason", "Harper", "Logan", "Evelyn", "Carter", "Abigail"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
    "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez"
]

ORDER_CATALOG = [
    {"code": "CBC", "name": "Complete Blood Count", "type": "LABORATORY", "unit": "10^3/uL", "range": "4.5-11.0", "normal_val": "7.2", "abnormal_val": "15.8"},
    {"code": "BMP", "name": "Basic Metabolic Panel", "type": "LABORATORY", "unit": "mg/dL", "range": "70-99", "normal_val": "88", "abnormal_val": "142"},
    {"code": "LIPID", "name": "Lipid Profile Panel", "type": "LABORATORY", "unit": "mg/dL", "range": "<200", "normal_val": "175", "abnormal_val": "260"},
    {"code": "TSH", "name": "Thyroid Stimulating Hormone", "type": "LABORATORY", "unit": "uIU/mL", "range": "0.4-4.0", "normal_val": "2.1", "abnormal_val": "8.5"},
    {"code": "HBA1C", "name": "Hemoglobin A1c Glycated", "type": "LABORATORY", "unit": "%", "range": "<5.7", "normal_val": "5.4", "abnormal_val": "9.1"},
    {"code": "UA", "name": "Urinalysis Complete", "type": "LABORATORY", "unit": "eval", "range": "Negative", "normal_val": "Negative", "abnormal_val": "Positive (Protein 2+)"}
]

def seed_database(random_seed: int = 42):
    random.seed(random_seed)
    logger.info(f"Starting deterministic database seeding (seed={random_seed})...")

    # Ensure schema is created fresh
    init_database()

    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.now()

        # 1. Seed Patients (50 patients)
        patient_ids = []
        logger.info("Seeding 50 synthetic patients...")
        for i in range(1, 51):
            fn = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
            ln = LAST_NAMES[(i * 3) % len(LAST_NAMES)]
            mrn = f"MRN-2026-{10000 + i}"
            dob_year = 1950 + (i * 7) % 50
            dob = f"{dob_year:04d}-{(i % 12) + 1:02d}-{(i % 27) + 1:02d}"
            gender = ["FEMALE", "MALE", "OTHER"][i % 3]
            phone = f"555-01{i:02d}"
            email = f"{fn.lower()}.{ln.lower()}{i}@synthetic-careflow.org"
            address = f"{100 + i} Medical Center Way, Suite {i}, Metro City"

            cursor.execute("""
            INSERT INTO PATIENTS (mrn, first_name, last_name, date_of_birth, gender, phone, email, address, status)
            VALUES (:mrn, :first_name, :last_name, :date_of_birth, :gender, :phone, :email, :address, 'ACTIVE')
            """, {
                "mrn": mrn, "first_name": fn, "last_name": ln, "date_of_birth": dob,
                "gender": gender, "phone": phone, "email": email, "address": address
            })
            patient_ids.append(i)

        # 2. Seed Appointments (120 appointments)
        logger.info("Seeding 120 clinical appointments...")
        appointment_ids = []
        statuses = ["SCHEDULED", "CHECKED_IN", "IN_PROGRESS", "COMPLETED", "CANCELLED", "NO_SHOW"]

        for i in range(1, 121):
            pid = patient_ids[i % len(patient_ids)]
            dept = DEPARTMENTS[i % len(DEPARTMENTS)]
            provider = PROVIDERS[dept][i % len(PROVIDERS[dept])]
            
            # Days offset: -5 to +2 days from now
            day_offset = (i % 8) - 5
            appt_dt = (now + timedelta(days=day_offset, hours=(8 + (i % 9)), minutes=(i * 15) % 60)).replace(microsecond=0)
            appt_time_str = appt_dt.isoformat()

            # Status distribution
            if day_offset < 0:
                status = random.choice(["COMPLETED", "COMPLETED", "CANCELLED", "NO_SHOW"])
            elif day_offset == 0:
                status = random.choice(["SCHEDULED", "CHECKED_IN", "IN_PROGRESS", "COMPLETED"])
            else:
                status = "SCHEDULED"

            check_in_time = None
            cancel_reason = None

            if status in ("CHECKED_IN", "IN_PROGRESS", "COMPLETED"):
                check_in_time = (appt_dt - timedelta(minutes=random.randint(5, 25))).isoformat()
            elif status == "CANCELLED":
                cancel_reason = random.choice(["Patient feeling unwell", "Conflict with work", "Transportation issue", "Rescheduled by provider"])

            cursor.execute("""
            INSERT INTO APPOINTMENTS (patient_id, appointment_time, appointment_type, department, provider_name, status, check_in_time, cancel_reason)
            VALUES (:pid, :time, 'FOLLOW_UP', :dept, :provider, :status, :check_in, :cancel_reason)
            """, {
                "pid": pid, "time": appt_time_str, "dept": dept, "provider": provider,
                "status": status, "check_in": check_in_time, "cancel_reason": cancel_reason
            })
            appointment_ids.append(i)

        # 3. Seed Encounters (85 encounters)
        logger.info("Seeding 85 clinical encounters...")
        encounter_ids = []
        for i in range(1, 86):
            appt_id = appointment_ids[i - 1]
            pid = patient_ids[(i - 1) % len(patient_ids)]
            dept = DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
            provider = PROVIDERS[dept][(i - 1) % len(PROVIDERS[dept])]

            start_dt = now - timedelta(days=(i % 6), hours=(i % 10), minutes=random.randint(10, 45))
            start_str = start_dt.isoformat()

            if i % 5 == 0:
                enc_status = "OPEN"
                end_str = None
            elif i % 5 == 1:
                enc_status = "IN_PROGRESS"
                end_str = None
            elif i % 5 == 2:
                enc_status = "AWAITING_RESULTS"
                end_str = None
            else:
                enc_status = "COMPLETED"
                end_str = (start_dt + timedelta(minutes=random.randint(20, 65))).isoformat()

            notes = f"Patient presented for clinical evaluation in {dept}. Vitals reviewed, examination unremarkable. Care plan formulated."

            cursor.execute("""
            INSERT INTO ENCOUNTERS (patient_id, appointment_id, encounter_type, department, provider_name, status, start_time, end_time, chief_complaint, clinical_notes)
            VALUES (:pid, :appt_id, 'OUTPATIENT', :dept, :provider, :status, :start_time, :end_time, 'Routine Follow-up & Evaluation', :notes)
            """, {
                "pid": pid, "appt_id": appt_id, "dept": dept, "provider": provider,
                "status": enc_status, "start_time": start_str, "end_time": end_str, "notes": notes
            })
            encounter_ids.append(i)

        # 4. Seed Observations / Vitals (170 observations)
        logger.info("Seeding 170 observations / vitals...")
        for i in range(1, 86):
            enc_id = encounter_ids[i - 1]
            pid = patient_ids[(i - 1) % len(patient_ids)]
            # Systolic BP
            sys_val = random.randint(110, 148)
            cursor.execute("""
            INSERT INTO OBSERVATIONS (encounter_id, patient_id, observation_type, observation_code, value_numeric, unit, source, status)
            VALUES (:enc_id, :pid, 'VITAL_SIGNS', 'BP_SYS', :val, 'mmHg', 'TRIAGE_STATION', 'FINAL')
            """, {"enc_id": enc_id, "pid": pid, "val": sys_val})

            # Heart Rate
            hr_val = random.randint(62, 95)
            cursor.execute("""
            INSERT INTO OBSERVATIONS (encounter_id, patient_id, observation_type, observation_code, value_numeric, unit, source, status)
            VALUES (:enc_id, :pid, 'VITAL_SIGNS', 'HEART_RATE', :val, 'bpm', 'TRIAGE_STATION', 'FINAL')
            """, {"enc_id": enc_id, "pid": pid, "val": hr_val})

        # 5. Seed Orders (100 orders) & Results
        logger.info("Seeding 100 clinical orders and results...")
        order_ids = []
        for i in range(1, 101):
            enc_id = encounter_ids[(i - 1) % len(encounter_ids)]
            pid = patient_ids[(i - 1) % len(patient_ids)]
            template = ORDER_CATALOG[(i - 1) % len(ORDER_CATALOG)]
            priority = "STAT" if (i % 7 == 0) else ("URGENT" if (i % 4 == 0) else "ROUTINE")
            
            order_dt = now - timedelta(days=(i % 5), hours=(i % 12) + 1)
            order_str = order_dt.isoformat()

            # Orders 1-75 completed, 76-100 still ORDERED or IN_PROGRESS
            if i <= 75:
                order_status = "COMPLETED"
                compl_dt = order_dt + timedelta(hours=random.uniform(0.8, 6.5))
                compl_str = compl_dt.isoformat()
            else:
                order_status = "IN_PROGRESS" if (i % 2 == 0) else "ORDERED"
                compl_str = None

            cursor.execute("""
            INSERT INTO ORDERS (encounter_id, patient_id, order_type, order_code, order_name, priority, ordered_by, order_status, ordered_at, completed_at)
            VALUES (:enc_id, :pid, :type, :code, :name, :priority, 'Dr. Sarah Chen, MD', :status, :ordered_at, :completed_at)
            """, {
                "enc_id": enc_id, "pid": pid, "type": template["type"], "code": template["code"],
                "name": template["name"], "priority": priority, "status": order_status,
                "ordered_at": order_str, "completed_at": compl_str
            })
            order_ids.append(i)

            # For completed orders, seed RESULT
            if order_status == "COMPLETED":
                is_abnormal = (i % 4 == 0)
                is_critical = (i % 15 == 0)
                if is_critical:
                    flag = "CRITICAL"
                    val = f"{template['abnormal_val']} [CRITICAL]"
                elif is_abnormal:
                    flag = "HIGH" if (i % 2 == 0) else "LOW"
                    val = template['abnormal_val']
                else:
                    flag = "NORMAL"
                    val = template['normal_val']

                res_status = "PENDING_REVIEW" if (i % 3 == 0) else "REVIEWED"
                rev_by = "Dr. Elena Rostova, MD" if res_status == "REVIEWED" else None
                rev_at = (compl_dt + timedelta(hours=1)).isoformat() if res_status == "REVIEWED" else None

                cursor.execute("""
                INSERT INTO RESULTS (order_id, result_value, reference_range, unit, abnormal_flag, result_status, reviewed_by, reviewed_at, result_time)
                VALUES (:oid, :val, :range, :unit, :flag, :res_status, :rev_by, :rev_at, :res_time)
                """, {
                    "oid": i, "val": val, "range": template["range"], "unit": template["unit"],
                    "flag": flag, "res_status": res_status, "rev_by": rev_by, "rev_at": rev_at,
                    "res_time": compl_str
                })

        # 6. Intentionally Seed 5 Controlled Data Quality Test Cases
        logger.info("Seeding 5 controlled Data Quality exception scenarios...")

        # Test Case 1: Appointment marked CHECKED_IN without check_in_time (Appointment 5)
        cursor.execute("UPDATE APPOINTMENTS SET status = 'CHECKED_IN', check_in_time = NULL WHERE appointment_id = 5")
        cursor.execute("""
        INSERT INTO DATA_QUALITY_ISSUES (rule_code, severity, affected_entity, entity_id, description, investigation_steps, resolution_status)
        VALUES ('DQ_MISSING_CHECKIN_TIME', 'HIGH', 'APPOINTMENT', 5,
                'Appointment 5 has status CHECKED_IN but check_in_time is NULL',
                'Inspect check-in audit logs; backfill arrival timestamp or reset state', 'OPEN')
        """)

        # Test Case 2: Order marked COMPLETED without completed_at (Order 12)
        cursor.execute("UPDATE ORDERS SET order_status = 'COMPLETED', completed_at = NULL WHERE order_id = 12")
        cursor.execute("""
        INSERT INTO DATA_QUALITY_ISSUES (rule_code, severity, affected_entity, entity_id, description, investigation_steps, resolution_status)
        VALUES ('DQ_MISSING_COMPLETION_TIME', 'MEDIUM', 'ORDER', 12,
                'Order 12 is marked COMPLETED but completed_at is NULL',
                'Check associated Result timestamp and backfill completed_at', 'OPEN')
        """)

        # Test Case 3: Completed Encounter with Active Pending Orders (Encounter 18)
        cursor.execute("UPDATE ENCOUNTERS SET status = 'COMPLETED' WHERE encounter_id = 18")
        cursor.execute("UPDATE ORDERS SET order_status = 'IN_PROGRESS' WHERE order_id = 18")
        cursor.execute("""
        INSERT INTO DATA_QUALITY_ISSUES (rule_code, severity, affected_entity, entity_id, description, investigation_steps, resolution_status)
        VALUES ('DQ_COMPLETED_ENC_WITH_PENDING_ORDERS', 'CRITICAL', 'ENCOUNTER', 18,
                'Encounter 18 is marked COMPLETED despite having an order in IN_PROGRESS status',
                'Determine whether lab test was performed or cancelled before visit signoff', 'OPEN')
        """)

        # Test Case 4: Encounter with end_time preceding start_time (Encounter 22)
        cursor.execute("""
        UPDATE ENCOUNTERS 
        SET start_time = '2026-10-25T14:30:00', end_time = '2026-10-25T14:00:00'
        WHERE encounter_id = 22
        """)
        cursor.execute("""
        INSERT INTO DATA_QUALITY_ISSUES (rule_code, severity, affected_entity, entity_id, description, investigation_steps, resolution_status)
        VALUES ('DQ_INVALID_TIMESTAMP_SEQUENCE', 'CRITICAL', 'ENCOUNTER', 22,
                'Encounter 22 end_time (14:00) precedes start_time (14:30)',
                'Inspect server clock synchronization and reception logs', 'OPEN')
        """)

        # Test Case 5: Resolved Data Quality Issue with audit record for demonstration
        cursor.execute("""
        INSERT INTO DATA_QUALITY_ISSUES (rule_code, severity, affected_entity, entity_id, description, investigation_steps, resolution_status, resolved_by, resolved_at, remediation_notes)
        VALUES ('DQ_MISSING_CHECKIN_TIME', 'HIGH', 'APPOINTMENT', 9,
                'Appointment 9 had missing check-in timestamp',
                'Check-in kiosk log was reviewed and time restored',
                'RESOLVED', 'Dr. Sarah Chen, MD', '2026-10-28T09:15:00', 'Timestamp verified from security badge terminal log.')
        """)

        # 7. Seed Initial Audit Logs
        logger.info("Seeding audit history...")
        cursor.execute("""
        INSERT INTO AUDIT_LOG (entity_type, entity_id, action, actor, previous_state, new_state, correlation_id, reason)
        VALUES ('SYSTEM', 1, 'DATABASE_SEED', 'SYSTEM_ADMIN', NULL, '{"dataset": "deterministic_synthetic_v1", "records": 450}', 'SEED-CORR-001', 'Initial environment provisioning')
        """)

        conn.commit()
        logger.info("Database seeding successfully completed!")

if __name__ == "__main__":
    seed_database()
