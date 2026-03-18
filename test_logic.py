import json
from logic import consolidate_attendance

def test_consolidation():
    mock_items = [
        # Employee 1: Perfect punctuality
        {"employee_id": "EMP001", "name": "Aarav Sharma", "date": "2026-03-18", "time": "09:00:00", "status": "IN"},
        {"employee_id": "EMP001", "name": "Aarav Sharma", "date": "2026-03-18", "time": "18:00:00", "status": "OUT"},
        
        # Employee 2: Late arrival (Strike 1)
        {"employee_id": "EMP002", "name": "Ishita Kapoor", "date": "2026-03-18", "time": "11:15:00", "status": "IN"},
        {"employee_id": "EMP002", "name": "Ishita Kapoor", "date": "2026-03-18", "time": "18:30:00", "status": "OUT"},
        
        # Employee 3: Missing punch
        {"employee_id": "EMP003", "name": "Rohan Verma", "date": "2026-03-18", "time": "10:00:00", "status": "IN"},
        # Missing OUT
        
        # Case variation: different field naming and extra punches
        {"EmployeeID": "EMP004", "Employee_Name": "Sanya Gupta", "Date": "2026-03-18", "Time": "12:00:00", "Status": "IN"},
        {"EmployeeID": "EMP004", "Employee_Name": "Sanya Gupta", "Date": "2026-03-18", "Time": "13:00:00", "Status": "OUT"},
        {"EmployeeID": "EMP004", "Employee_Name": "Sanya Gupta", "Date": "2026-03-18", "Time": "09:15:00", "Status": "IN"}, # Earlier IN
        {"EmployeeID": "EMP004", "Employee_Name": "Sanya Gupta", "Date": "2026-03-18", "Time": "19:00:00", "Status": "OUT"}, # Later OUT
    ]

    results = consolidate_attendance(mock_items)
    
    # Sort results by employee_id for easier validation
    results.sort(key=lambda x: x['employee_id'])

    expected = [
        {"id": "EMP001", "late": False, "missing": False, "p_count": 2},
        {"id": "EMP002", "late": True,  "missing": False, "p_count": 2},
        {"id": "EMP003", "late": False, "missing": True,  "p_count": 1},
        {"id": "EMP004", "late": False, "missing": False, "p_count": 4}, # check_in should be 09:15:00
    ]

    print("Verifying results...")
    for i, exp in enumerate(expected):
        res = results[i]
        assert res['employee_id'] == exp['id']
        assert res['late_flag'] == exp['late'], f"Late flag mismatch for {res['employee_id']}"
        assert res['missing_punch'] == exp['missing'], f"Missing punch mismatch for {res['employee_id']}"
        assert res['raw_punch_count'] == exp['p_count'], f"Punch count mismatch for {res['employee_id']}"
        print(f"[OK] {res['employee_id']} passed.")

    # Check timestamps for EMP004 (earliest IN / latest OUT)
    emp004 = results[3]
    assert "09:15:00" in emp004['check_in'], f"Expected 09:15:00 IN, got {emp004['check_in']}"
    assert "19:00:00" in emp004['check_out'], f"Expected 19:00:00 OUT, got {emp004['check_out']}"
    print(f"[OK] EMP004 timestamps verified: IN={emp004['check_in']}, OUT={emp004['check_out']}")

    print("\nAll tests passed successfully!")

if __name__ == "__main__":
    test_consolidation()
