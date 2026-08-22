"""Run one land() and be killed part-way through. Used only by check_04.

The line printed on standard output before land() is called is a starting gun.
Without it the check would time its kill from the moment the process started,
and almost all of that time is the interpreter importing pandas — so every kill
landed before land() had written a byte, and ten subprocesses tested nothing.
The check waits for the line, then times the kill from there.
"""
import sys, pathlib, importlib.util

REPOSITORY = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPOSITORY))

spec = importlib.util.spec_from_file_location(
    "lab04", REPOSITORY / "labs" / "04_survive_the_kill.py")
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)

destination = pathlib.Path(sys.argv[1])
count = int(sys.argv[2])
records = [{"n": n, "filler": "x" * 400} for n in range(count)]

# Everything expensive is done. From here on the clock measures land() itself.
print("ready", flush=True)

lab.land(records, destination)
