import os, shutil
from database import *

BASE = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE, 'static', 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

backup = os.path.join(BASE, '.static_backup')
if os.path.isdir(backup) and not os.listdir(UPLOAD_FOLDER):
    for f in os.listdir(backup):
        shutil.copy(os.path.join(backup, f), os.path.join(UPLOAD_FOLDER, f))

drop_tables()
initialize_db()
create_tables_roles()
pop_from_json()

