import atexit
import os
import shelve
from pathlib import Path

dirname = os.getenv('DB_PATH')
Path(dirname).mkdir(exist_ok=True)

db = shelve.open(os.path.join(dirname, 'db'))
atexit.register(db.close)
