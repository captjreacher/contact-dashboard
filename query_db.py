import sqlite3

conn = sqlite3.connect('database/app.db')
c = conn.cursor()
c.execute("SELECT first_name, last_name, email_address, phone_number, validation_status, validation_errors FROM contacts")
for row in c.fetchall():
    print(row)
conn.close()
