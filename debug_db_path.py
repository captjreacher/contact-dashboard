import os

current_file_path = os.path.abspath(__file__)
project_root = os.path.dirname(current_file_path)
db_path = os.path.join(project_root, "database", "app.db")

print("Full DB path:", db_path)
