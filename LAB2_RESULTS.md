# Lab 2: Unit Testing & Fixture Engineering — Execution Results

**Course:** Cybersecurity Engineering — DevOps & Quality Engineering  
**Project:** FastAPI EventManager API — Isolated Testing & Pair Collaboration  
**Instructor:** Smaali Sahar  
**Repository:** [https://github.com/smaaliSahar/EventManager-Pair11](https://github.com/smaaliSahar/EventManager-Pair11)  
**Pair:** Student A (`SMARIfiras`) & Student B (`soheib2004`)  

---

## 1. Test Suite Execution (`pytest -v`)

### Command
```powershell
pytest -v
```

### Terminal Output
```text
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.7.0 -- C:\Users\fifou\Documents\DevOps\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\fifou\Documents\DevOps
plugins: anyio-4.15.1, cov-7.1.0
collecting ... collected 20 items

tests/test_events.py::test_valid_event PASSED                            [  5%]
tests/test_events.py::test_filter_by_location PASSED                     [ 10%]
tests/test_events.py::test_filter_by_title PASSED                        [ 15%]
tests/test_events.py::test_minimum_capacity PASSED                       [ 20%]
tests/test_events.py::test_maximum_capacity PASSED                       [ 25%]
tests/test_events.py::test_minimum_title_length PASSED                   [ 30%]
tests/test_events.py::test_short_title_rejected PASSED                   [ 35%]
tests/test_events.py::test_zero_capacity_rejected PASSED                 [ 40%]
tests/test_events.py::test_negative_capacity_rejected PASSED             [ 45%]
tests/test_events.py::test_excessive_capacity_rejected PASSED            [ 50%]
tests/test_participants.py::test_valid_participant PASSED                [ 55%]
tests/test_participants.py::test_has_available_capacity_success PASSED   [ 60%]
tests/test_participants.py::test_check_duplicate_registration_success PASSED [ 65%]
tests/test_participants.py::test_capacity_boundary_below_max PASSED      [ 70%]
tests/test_participants.py::test_capacity_boundary_at_max PASSED         [ 75%]
tests/test_participants.py::test_capacity_boundary_above_max PASSED      [ 80%]
tests/test_participants.py::test_minimum_name_length PASSED              [ 85%]
tests/test_participants.py::test_short_name_rejected PASSED              [ 90%]
tests/test_participants.py::test_invalid_email_rejected PASSED           [ 95%]
tests/test_participants.py::test_duplicate_registration_raises_error PASSED [100%]

============================= 20 passed in 0.20s ==============================
```

---

## 2. Test Filtering by Keyword (`pytest -k "capacity or title"`)

### Command
```powershell
pytest -k "capacity or title"
```

### Terminal Output
```text
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\fifou\Documents\DevOps
plugins: anyio-4.15.1, cov-7.1.0
collected 20 items / 8 deselected / 12 selected

tests\test_events.py ........                                            [ 66%]
tests\test_participants.py ....                                          [100%]

====================== 12 passed, 8 deselected in 0.19s =======================
```

---

## 3. Code Coverage Report (`pytest --cov=app --cov-report=term-missing`)

### Command
```powershell
pytest --cov=app --cov-report=term-missing
```

### Terminal Output
```text
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\fifou\Documents\DevOps
plugins: anyio-4.15.1, cov-7.1.0
collected 20 items

tests\test_events.py ..........                                          [ 50%]
tests\test_participants.py ..........                                    [100%]

=============================== tests coverage ================================
_______________ coverage: platform win32, python 3.13.2-final-0 _______________

Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
app\__init__.py                    0      0   100%
app\database.py                   11     11     0%   1-26
app\main.py                       11     11     0%   1-23
app\models.py                     26     26     0%   1-65
app\routers\__init__.py            0      0   100%
app\routers\events.py             50     50     0%   1-143
app\routers\participants.py       32     32     0%   1-108
app\routers\registrations.py      30     30     0%   1-105
app\schemas.py                    26      0   100%
app\utils.py                      10      0   100%
------------------------------------------------------------
TOTAL                            196    160    18%
============================= 20 passed in 0.44s ==============================
```

> **Note on Coverage:**  
> The target modules under pure unit testing (`app/schemas.py` and `app/utils.py`) achieved **100% coverage**. Database and HTTP router files were purposefully isolated with zero calls per the lab rule: *"No live database or HTTP network calls during unit tests."*

---

## 4. Git Collaboration & Feature Branch Merges

### Command
```powershell
git log --graph --oneline --all
```

### Terminal Output
```text
*   915c9c5 Merge pull request from feature/student-b-participants (Student B: Participant Tests)
|\  
| * 29ace77 feat(tests): implement Student B participant logic and duplicate guard unit tests
* |   cbb8e43 Merge pull request from feature/student-a-events (Student A: Event Tests)
|\ \  
| |/  
|/|   
| * eda74f8 feat(tests): fix and complete Student A event schema and search unit tests
|/  
*   25d8a43 feat: add new files and code
|\  
| *   4ba6913 Merge branch 'main' of https://github.com/smaaliSahar/EventManager-Pair11
| |\  
| * | 3248af7 feat: add event searching by title
* | | 73385bf feat: add new project files
| |/  
|/|   
* | c8e25ed feat: add event filtering by location
|/  
* aafdf50 Initial Event Manager project
```

### Remote Branches Status
```text
origin/main                     (up to date, SHA: 915c9c5)
origin/feature/student-a-events (up to date, SHA: eda74f8)
origin/feature/student-b-participants (up to date, SHA: 29ace77)
```
