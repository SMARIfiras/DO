# Code Coverage Comparison: Lab 2 vs. Lab 3

**Course:** Cybersecurity Engineering — DevOps & Quality Engineering  
**Project:** FastAPI EventManager Backend  
**Instructor:** Smaali Sahar  
**Repository:** [https://github.com/smaaliSahar/EventManager-Pair11](https://github.com/smaaliSahar/EventManager-Pair11)  
**Pair:** Student A (`SMARIfiras`) & Student B (`soheib2004`)  

---

## 1. Global Coverage Summary

| Metric | Lab 2 Results | Lab 3 Results | Evolution / Delta |
|---|:---:|:---:|:---:|
| **Total Statements** | 196 | 193 | -3 (cleanups) |
| **Executed Statements** | 36 | **193** | **+157 statements** |
| **Missed Statements** | 160 | **0** | **-160 missed lines** |
| **Total Line Coverage** | **18%** | **100%** | **+82% absolute gain** |
| **Lab Minimum Requirement** | N/A | $\ge 85\%$ | **Exceeded (+15%)** |
| **Evaluation Status** | Baseline | **100% Comprehensive** | **PASSED** |

---

## 2. Module-by-Module Coverage Comparison Table

| Module File | Lab 2 Stmts | Lab 2 Miss | Lab 2 Cover | Lab 3 Stmts | Lab 3 Miss | Lab 3 Cover | Coverage Delta | Uncovered Lines in Lab 2 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| `app/__init__.py` | 0 | 0 | **100%** | 0 | 0 | **100%** | 0% | None |
| `app/database.py` | 11 | 11 | **0%** | 11 | 0 | **100%** | **+100%** | Lines `1-26` (now 100% covered) |
| `app/main.py` | 11 | 11 | **0%** | 11 | 0 | **100%** | **+100%** | Lines `1-23` (now 100% covered) |
| `app/models.py` | 26 | 26 | **0%** | 26 | 0 | **100%** | **+100%** | Lines `1-65` (now 100% covered) |
| `app/routers/__init__.py` | 0 | 0 | **100%** | 0 | 0 | **100%** | 0% | None |
| `app/routers/events.py` | 50 | 50 | **0%** | 50 | 0 | **100%** | **+100%** | Lines `1-143` (now 100% covered) |
| `app/routers/participants.py` | 32 | 32 | **0%** | 32 | 0 | **100%** | **+100%** | Lines `1-108` (now 100% covered) |
| `app/routers/registrations.py` | 30 | 30 | **0%** | 30 | 0 | **100%** | **+100%** | Lines `1-105` (now 100% covered) |
| `app/schemas.py` | 26 | 0 | **100%** | 23 | 0 | **100%** | 0% | Fully maintained |
| `app/utils.py` | 10 | 0 | **100%** | 10 | 0 | **100%** | 0% | Fully maintained |
| **TOTAL** | **196** | **160** | **18%** | **193** | **0** | **100%** | **+82%** | **All 160 previously missing lines are now tested** |

---

## 3. Terminal Execution Reports Comparison

### Lab 2 Terminal Output (`pytest --cov=app --cov-report=term-missing`)
```text
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

### Lab 3 Terminal Output (`pytest --cov=app --cov-report=term-missing`)
```text
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

## 4. Key Takeaways

1. **Massive Coverage Jump (+82%)**: Overall line coverage increased from **18%** to **100%**.
2. **Elimination of Uncovered Modules**: In Lab 2, 6 modules (`database.py`, `main.py`, `models.py`, `events.py`, `participants.py`, `registrations.py`) had **0% coverage**. In Lab 3, all 6 modules achieved **100% coverage**.
3. **Target Exceeded**: Lab 3 required $\ge 85\%$ line coverage; the test suite reached **100%** coverage with zero missed lines.
