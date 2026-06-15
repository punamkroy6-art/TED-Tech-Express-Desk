import sys
import os
import asyncio
from datetime import datetime

# Resolve sys.path so we can import app models and database configuration directly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import AsyncSessionLocal
from app.models.employee import Employee
from app.models.error_pattern import ErrorPattern
from app.models.session import Session
from app.models.diagnosis import DiagnosisResult
from app.models.audit_log import AuditLog
from sqlalchemy import select

async def run_data_tests():
    print(f"[{datetime.now()}] Initiating database integrity tests...")
    
    async with AsyncSessionLocal() as session:
        # Test 1: Fetch and Verify Employees
        print("\n--- Test 1: Querying Employees ---")
        stmt_emp = select(Employee).order_by(Employee.employee_id)
        result_emp = await session.execute(stmt_emp)
        employees = result_emp.scalars().all()
        
        assert len(employees) >= 3, f"Expected at least 3 employees, got {len(employees)}"
        print(f"[OK] Successfully retrieved {len(employees)} employees:")
        for emp in employees:
            print(f"  - [{emp.employee_id}] {emp.display_name} ({emp.department})")
            assert emp.email is not None, "Employee email should not be None"
            assert "@" in emp.email, "Invalid email format"
        
        # Test 2: Fetch and Verify Error Patterns (verifies SQLiteCompatibleArray and JSON)
        print("\n--- Test 2: Querying Error Patterns (Hybrid Array + JSON) ---")
        stmt_err = select(ErrorPattern).order_by(ErrorPattern.error_code)
        result_err = await session.execute(stmt_err)
        patterns = result_err.scalars().all()
        
        assert len(patterns) >= 3, f"Expected at least 3 error patterns, got {len(patterns)}"
        print(f"[OK] Successfully retrieved {len(patterns)} error patterns:")
        for pat in patterns:
            print(f"  - [{pat.error_code}] {pat.description} ({pat.severity})")
            
            # CRITICAL: Verify that SQLiteCompatibleArray successfully deserialized back into a Python list
            print(f"    * Keywords (Array Type): {pat.keywords} (Type: {type(pat.keywords)})")
            assert isinstance(pat.keywords, list), f"Keywords should be a Python list, got {type(pat.keywords)}"
            assert len(pat.keywords) > 0, "Keywords array should not be empty"
            
            # Verify JSON deserialization of fix_steps
            print(f"    * Fix Steps (JSON Type): {len(pat.fix_steps)} steps loaded")
            assert isinstance(pat.fix_steps, list), f"Fix steps should be a JSON list, got {type(pat.fix_steps)}"
            assert "step" in pat.fix_steps[0], "Fix step dictionary structure should contain 'step' key"
            
        # Test 3: Fetch and Verify Session Relationships
        print("\n--- Test 3: Querying Sessions and Relationships ---")
        stmt_sess = select(Session).filter(Session.employee_id == "EMP-1029")
        result_sess = await session.execute(stmt_sess)
        db_session = result_sess.scalars().first()
        
        assert db_session is not None, "Expected session for EMP-1029"
        print(f"[OK] Successfully retrieved session {db_session.id}:")
        print(f"  - Kiosk ID: {db_session.kiosk_id}")
        print(f"  - Auth Method: {db_session.auth_method}")
        print(f"  - CSAT Score: {db_session.csat_score}")
        assert db_session.csat_score == 5, f"Expected CSAT 5, got {db_session.csat_score}"
        
        # Test 4: Fetch and Verify AI Diagnosis Results
        print("\n--- Test 4: Querying AI Diagnosis Results ---")
        stmt_diag = select(DiagnosisResult).filter(DiagnosisResult.session_id == db_session.id)
        result_diag = await session.execute(stmt_diag)
        diag = result_diag.scalars().first()
        
        assert diag is not None, "Expected diagnosis result for session"
        print(f"[OK] Successfully retrieved AI Diagnosis Result {diag.id}:")
        print(f"  - Error input text: '{diag.input_error_text}'")
        print(f"  - Confidence: {diag.confidence:.2f}")
        print(f"  - Suggested Group: {diag.suggested_group}")
        
        # Verify JSON conversions on complex fields
        assert isinstance(diag.input_device_info, dict), "Device info should be parsed as dictionary"
        assert isinstance(diag.fix_steps, list), "Fix steps should be parsed as list"
        assert isinstance(diag.kb_references, list), "KB references should be parsed as list"
        print(f"    * Device OS: {diag.input_device_info.get('os')} ({diag.input_device_info.get('model')})")
        print(f"    * Fix checklist: {diag.fix_steps}")
        print(f"    * Reference KB Title: '{diag.kb_references[0].get('title')}'")

    print("\n=======================================================")
    print("SUCCESS: ALL DATABASE INTEGRITY TESTS PASSED SUCCESSFULLY!")
    print("=======================================================\n")

if __name__ == "__main__":
    asyncio.run(run_data_tests())
