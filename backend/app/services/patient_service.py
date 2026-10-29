from datetime import datetime
import random
from typing import Dict, Any, Optional
from ..repositories.patient_repo import PatientRepository
from ..repositories.audit_repo import AuditRepository
from ..schemas.patient import PatientCreate, PatientUpdate, PatientResponse, PatientListResponse
from ..core.exceptions import ResourceNotFoundException, DataIntegrityException

class PatientService:
    def __init__(self, conn):
        self.conn = conn
        self.repo = PatientRepository(conn)
        self.audit_repo = AuditRepository(conn)

    def _generate_mrn(self) -> str:
        year = datetime.now().year
        rand_num = random.randint(10000, 99999)
        return f"MRN-{year}-{rand_num}"

    def register_patient(self, payload: PatientCreate, actor: str = "REGISTRAR") -> PatientResponse:
        mrn = payload.mrn or self._generate_mrn()
        
        # Check duplicate MRN
        existing = self.repo.get_by_mrn(mrn)
        if existing:
            raise DataIntegrityException(
                message=f"A patient with Medical Record Number '{mrn}' already exists.",
                details={"mrn": mrn}
            )

        data = {
            "mrn": mrn,
            "first_name": payload.first_name.strip(),
            "last_name": payload.last_name.strip(),
            "date_of_birth": payload.date_of_birth,
            "gender": payload.gender,
            "phone": payload.phone,
            "email": payload.email,
            "address": payload.address,
            "status": "ACTIVE"
        }

        patient_id = self.repo.create(data)
        self.audit_repo.log_audit(
            entity_type="PATIENT",
            entity_id=patient_id,
            action="REGISTER_PATIENT",
            actor=actor,
            previous_state=None,
            new_state=data,
            reason="Initial patient registration"
        )
        self.conn.commit()

        created = self.repo.get_by_id(patient_id)
        return PatientResponse(**created)

    def update_patient(self, patient_id: int, payload: PatientUpdate, actor: str = "REGISTRAR") -> PatientResponse:
        existing = self.repo.get_by_id(patient_id)
        if not existing:
            raise ResourceNotFoundException("Patient", patient_id)

        updates = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
        if updates:
            self.repo.update(patient_id, updates)
            self.audit_repo.log_audit(
                entity_type="PATIENT",
                entity_id=patient_id,
                action="UPDATE_PATIENT",
                actor=actor,
                previous_state=existing,
                new_state=updates,
                reason="Demographics or contact update"
            )
            self.conn.commit()

        updated = self.repo.get_by_id(patient_id)
        return PatientResponse(**updated)

    def get_patient(self, patient_id: int) -> PatientResponse:
        patient = self.repo.get_by_id(patient_id)
        if not patient:
            raise ResourceNotFoundException("Patient", patient_id)
        return PatientResponse(**patient)

    def list_patients(self, search: Optional[str] = None, status: Optional[str] = None,
                      page: int = 1, page_size: int = 50) -> PatientListResponse:
        offset = (page - 1) * page_size
        items_raw = self.repo.list_patients(search=search, status=status, limit=page_size, offset=offset)
        total = self.repo.count_patients(search=search, status=status)
        items = [PatientResponse(**r) for r in items_raw]
        return PatientListResponse(items=items, total=total, page=page, page_size=page_size)
