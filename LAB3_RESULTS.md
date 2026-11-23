# Lab 3: Code Coverage & Mutation Testing — Execution Results

**Course:** Cybersecurity Engineering — DevOps & Quality Engineering  
**Project:** FastAPI EventManager API — Evaluating Test Quality with Pytest-Cov & Mutmut  
**Instructor:** Smaali Sahar  
**Repository:** [https://github.com/smaaliSahar/EventManager-Pair11](https://github.com/smaaliSahar/EventManager-Pair11)  
**Pair:** Student A (`SMARIfiras`) & Student B (`soheib2004`)  

---

## 1. Quality Framework Summary

| Quality Layer | Tooling | Core Question Addressed | Target Metric | Achieved Metric | Status |
|---|---|---|---|---|---|
| **Layer 1: Line Coverage** | `pytest-cov` | Which lines of source code were executed during test runs? | $\ge 85\%$ | **100%** (193/193 statements) | **PASSED** |
| **Layer 2: Mutation Testing** | `mutmut` | Will tests actually fail if bugs are introduced into source code? | $\ge 80\%$ | **100.00%** (204/204 mutants killed) | **PASSED** |

---

## 2. Section 1: Code Coverage Report (`pytest-cov`)

### Command
```powershell
pytest --cov=app --cov-report=term-missing --cov-report=html
```

### Coverage Execution Output
```text
=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.14.4-final-0 _______________

Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
app\__init__.py                    0      0   100%
app\database.py                   11      0   100%
app\main.py                       11      0   100%
app\models.py                     26      0   100%
app\routers\__init__.py            0      0   100%
app\routers\events.py             50      0   100%
app\routers\participants.py       32      0   100%
app\routers\registrations.py      30      0   100%
app\schemas.py                    23      0   100%
app\utils.py                      10      0   100%
------------------------------------------------------------
TOTAL                            193      0   100%
Coverage HTML written to dir htmlcov
============================= 46 passed in 4.81s ==============================
```

---

## 3. Section 2: Mutation Testing Report (`mutmut`)

### Configuration (`setup.cfg`)
```ini
[mutmut]
paths_to_mutate = app/
runner = pytest
tests_dir = tests/
```

### Execution Command
```powershell
mutmut run
mutmut results
```

### Mutation Results Summary
```text
Legend:
🎉 Killed mutants:   204
⏰ Timeout:            0
🤔 Suspicious:         0
🙁 Survived:           0
🔇 Skipped:            0

Total Mutants:   204
Killed Mutants:  204
Survived:        0
Mutation Score:  100.00%
```

---

## 4. Student Pair Task Division & Verification

### Student A Tasks (Events Domain — `tests/test_events.py`):
- [x] **Boundary Mutants**: Killed capacity mutants (`capacity > 10000` to `>=`) with boundary tests for `capacity=10000`, `capacity=1`, `capacity=0`, and `capacity=10001`.
- [x] **String Length Mutants**: Killed title validation mutants (`min_length=3` vs 2) with tests for length 2 (`"AB"` rejected) and length 3 (`"ABC"` accepted).
- [x] **Search Filter Mutants**: Killed casefold/lower mutants in `filter_events_by_title` and `filter_events_by_location` with mixed-case search queries (`"pYtHoN"`, `"cYbEr"`, `"cOnStAnTiNe"`).
- [x] **Event Lifecycle & Date Guards**: Tested POST, GET, PUT, and DELETE with future, today (`date.today()`), and past dates, verifying exact HTTP exception details and query filtering.
- [x] **Event Schema & Model Defaults**: Verified model indices, nullability, column lengths, and ORM conversion (`from_attributes=True`).

### Student B Tasks (Participants & Registration Domain — `tests/test_participants.py`):
- [x] **Capacity Guard Mutants**: Killed capacity guard mutants (`current_count < max_capacity` altered to `<=`) by testing boundary conditions at equal count, zero capacity, and over-capacity registration attempts (HTTP 409).
- [x] **Duplicate Check Mutants**: Killed duplicate registration mutants in both utility functions (`match="^Participant already registered$"`) and API endpoints (HTTP 409 conflict).
- [x] **Email Format Mutants**: Killed regex/validation mutants by testing an extensive parameterized matrix of invalid email formats (`"plainaddress"`, `"@missingusername.com"`, `"missingdomain@"`, `"missingdot@domain"`, `"user with spaces@domain.com"`, `"two@@domain.com"`).
- [x] **Name Length Boundaries**: Verified exact boundary of max length 100 (`len(name) == 100` accepted, 101 rejected).
- [x] **Database & Concurrency Integrity**: Verified SQLite thread concurrency (`check_same_thread=False`), generator lifecycle (`get_db`), session properties, and metadata constraints.

---

## 5. Submission Checklist

- [x] `setup.cfg` committed to repository root.
- [x] Achieved $\ge 85\%$ Code Coverage (**100% achieved**).
- [x] Achieved $\ge 80\%$ Mutation Score (**100.00% achieved**).
- [x] All commits and Pull Requests pushed and merged to `main`.
