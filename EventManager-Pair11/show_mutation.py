import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import mutmut.cache
from pony.orm import db_session
from mutmut.cache import Mutant, OK_KILLED, BAD_SURVIVED, BAD_TIMEOUT

mutmut.cache.print_result_cache()

with db_session:
    total = Mutant.select().count()
    killed = Mutant.select(lambda m: m.status == OK_KILLED).count()
    survived = Mutant.select(lambda m: m.status == BAD_SURVIVED).count()
    timeout = Mutant.select(lambda m: m.status == BAD_TIMEOUT).count()

    print("\n" + "=" * 45)
    print("        MUTATION TESTING RESULTS (mutmut)")
    print("=" * 45)
    print(f" Total Mutants:    {total}")
    print(f" Killed Mutants:   {killed} (PASSED)")
    print(f" Survived Mutants: {survived}")
    print(f" Timeout Mutants:  {timeout}")
    if total > 0:
        score = (killed / total) * 100
        print(f" Mutation Score:   {score:.2f}%")
    print("=" * 45 + "\n")
