import atexit
import shelve
import sys
import os
from pathlib import Path

dirname = os.path.join(os.path.dirname(sys.argv[0]), '../db')
Path(dirname).mkdir(exist_ok=True)

db = shelve.open(os.path.join(dirname, 'db'))
atexit.register(db.close)
