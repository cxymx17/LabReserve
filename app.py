from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'data.db'

def init_db():
    if not os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as con:
            cur = con.cursor()
            # Labs Table
            cur.execute('''CREATE TABLE labs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            )''')
            # Time Slots Table
            cur.execute('''CREATE TABLE slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lab_id INTEGER,
                time TEXT,
                reserved INTEGER DEFAULT 0,
                FOREIGN KEY(lab_id) REFERENCES labs(id)
            )''')
            # Insert sample labs
            labs = [('Lab A',), ('Lab B',), ('Lab C',)]
            cur.executemany('INSERT INTO labs (name) VALUES (?)', labs)
            # Insert time slots for each lab
            times = [f"{h}:00 - {h+1}:00" for h in range(9, 17)]
            for lab_id in range(1, 4):
                cur.executemany('INSERT INTO slots (lab_id, time) VALUES (?, ?)', [(lab_id, t) for t in times])
            con.commit()

def get_db():
    return sqlite3.connect(DATABASE)

@app.route('/')
def index():
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT * FROM labs')
    labs = cur.fetchall()
    # For each lab, fetch its slots
    lab_slots = []
    for lab in labs:
        cur.execute('SELECT * FROM slots WHERE lab_id=?', (lab[0],))
        slots = cur.fetchall()
        lab_slots.append((lab, slots))
    con.close()
    return render_template('index.html', lab_slots=lab_slots)

@app.route('/reserve/<int:slot_id>', methods=['GET', 'POST'])
def reserve(slot_id):
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT * FROM slots WHERE id=?', (slot_id,))
    slot = cur.fetchone()
    if not slot:
        flash('Slot not found.')
        return redirect(url_for('index'))
    if slot[3] == 1:
        flash('Slot already reserved.')
        return redirect(url_for('index'))
    if request.method == 'POST':
        # Reserve it
        cur.execute('UPDATE slots SET reserved=1 WHERE id=?', (slot_id,))
        con.commit()
        con.close()
        return render_template('confirm.html', action='reserved')
    # GET: show confirmation page
    con.close()
    return render_template('reserve.html', slot=slot)

@app.route('/cancel/<int:slot_id>', methods=['POST'])
def cancel(slot_id):
    con = get_db()
    cur = con.cursor()
    cur.execute('SELECT * FROM slots WHERE id=?', (slot_id,))
    slot = cur.fetchone()
    if not slot:
        flash('Slot not found.')
    elif slot[3] == 0:
        flash('Slot is not reserved.')
    else:
        cur.execute('UPDATE slots SET reserved=0 WHERE id=?', (slot_id,))
        flash('Reservation cancelled.')
        con.commit()
    con.close()
    return render_template('confirm.html', action='cancelled')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
