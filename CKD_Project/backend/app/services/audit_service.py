import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.entities import AuditLog
from backend.app.database.session import get_mongo_db

def record_audit_event(
    db: Session,
    user_id: Optional[int],
    role_name: Optional[str],
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    status: str = "SUCCESS"
):
    """Records an audit event in relational database and optionally in MongoDB."""
    try:
        log_entry = AuditLog(
            user_id=user_id,
            role_name=role_name,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id else None,
            details=details,
            ip_address=ip_address,
            status=status,
            created_at=datetime.datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"[Audit Log Error]: {e}")
        db.rollback()

    # Log to MongoDB if enabled
    mongo = get_mongo_db()
    if mongo is not None:
        try:
            mongo.audit_logs.insert_one({
                "user_id": user_id,
                "role_name": role_name,
                "action": action,
                "resource": resource,
                "resource_id": str(resource_id) if resource_id else None,
                "details": details,
                "ip_address": ip_address,
                "status": status,
                "timestamp": datetime.datetime.utcnow()
            })
        except Exception as e:
            print(f"[MongoDB Audit Error]: {e}")
