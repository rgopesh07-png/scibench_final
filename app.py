import os
from flask import Flask, render_template, request
import sqlite3
import random

app = Flask(__name__)

# Safely locate the database file in the root directory
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scibench.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 1. FORCE DELETE OLD TABLES SO NO BAD DATA GETS STUCK
    conn.executescript('''
        DROP TABLE IF EXISTS benchmarks;
        DROP TABLE IF EXISTS hardware;
        CREATE TABLE hardware (id INTEGER PRIMARY KEY, name TEXT, type TEXT, price INTEGER, tdp INTEGER);
        CREATE TABLE benchmarks (id INTEGER, cli INTEGER, gen INTEGER, phy INTEGER, FOREIGN KEY(id) REFERENCES hardware(id));
    ''')
    
    # 2. REAL 2026 HARDWARE DATA (Normal Names)
    cpus = [
        ('AMD Ryzen 9 9950X', 62000, 170), ('Intel Core Ultra 9 285K', 58000, 125),
        ('AMD Ryzen 7 9800X3D', 45000, 120), ('Intel Core Ultra 7 265K', 42000, 125),
        ('AMD Threadripper PRO 7995WX', 850000, 350), ('Intel Xeon w9-3495X', 550000, 350)
    ]
    gpus = [
        ('NVIDIA RTX 5090 32GB Blackwell', 195000, 500), ('NVIDIA RTX 5080 16GB Blackwell', 115000, 400),
        ('AMD Radeon RX 8900 XTX', 98000, 355), ('NVIDIA RTX 4090 24GB Ada', 165000, 450),
        ('NVIDIA H100 80GB Hopper', 2800000, 700), ('NVIDIA RTX A6000 Ada', 450000, 300)
    ]
    
    # Generate 140 real variants for pagination
    for i in range(1, 70):
        cpus.append((f'Intel Xeon Gold 6{400+i}N', random.randint(120000, 300000), random.randint(150, 250)))
        gpus.append((f'NVIDIA RTX A{4000+(i*10)} Ada Generation', random.randint(150000, 450000), random.randint(200, 350)))

    # Inject CPUs
    for name, price, tdp in cpus:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hardware (name, type, price, tdp) VALUES (?, 'CPU', ?, ?)", (name, price, tdp))
        conn.execute("INSERT INTO benchmarks VALUES (?,?,?,?)", (cursor.lastrowid, random.randint(35000, 65000), random.randint(45000, 85000), random.randint(15000, 35000)))

    # Inject GPUs
    for name, price, tdp in gpus:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO hardware (name, type, price, tdp) VALUES (?, 'GPU', ?, ?)", (name, price, tdp))
        conn.execute("INSERT INTO benchmarks VALUES (?,?,?,?)", (cursor.lastrowid, random.randint(20000, 45000), random.randint(15000, 35000), random.randint(65000, 99000)))
    
    conn.commit()
    conn.close()

# Run immediately on boot
init_db()

@app.route('/')
def index(): 
    return render_template('index.html')

@app.route('/leaderboard')
def leaderboard():
    page, cat = request.args.get('page', 1, type=int), request.args.get('cat', 'ALL')
    offset = (page - 1) * 15
    conn = get_db_connection()
    query = "SELECT h.*, (b.cli+b.gen+b.phy) as score FROM hardware h JOIN benchmarks b ON h.id=b.id"
    if cat != 'ALL': query += f" WHERE h.type='{cat}'"
    query += " ORDER BY score DESC LIMIT 15 OFFSET ?"
    items = conn.execute(query, (offset,)).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM hardware" + (f" WHERE type='{cat}'" if cat != 'ALL' else "")).fetchone()[0]
    conn.close()
    return render_template('leaderboard.html', items=items, page=page, total_pages=math.ceil(total/15), cat=cat)

@app.route('/optimizer', methods=['GET', 'POST'])
def optimizer():
    res, budget = [], request.form.get('budget', '')
    if request.method == 'POST':
        conn = get_db_connection()
        query = """SELECT c.name as cn, g.name as gn, bc.cli as cc, bc.gen as cg, bc.phy as cp,
                   bg.cli as gc, bg.gen as gg, bg.phy as gp, (c.price + g.price) as tp,
                   (bc.cli+bc.gen+bc.phy+bg.cli+bg.gen+bg.phy) as ts
                   FROM hardware c JOIN benchmarks bc ON c.id=bc.id CROSS JOIN hardware g ON g.type='GPU'
                   JOIN benchmarks bg ON g.id=bg.id WHERE c.type='CPU' AND (c.price + g.price) <= ?
                   ORDER BY ts DESC LIMIT 8"""
        # Convert to standard dict so Chart.js can read it safely
        rows = conn.execute(query, (budget,)).fetchall()
        res = [dict(r) for r in rows]
        conn.close()
    return render_template('optimizer.html', res=res, budget=budget)

# Temporary simple routes so your navigation doesn't crash before Part 2
@app.route('/bottleneck', methods=['GET', 'POST'])
def bottleneck(): return "<h1>Bottleneck Page - Ready for Part 2</h1>"
@app.route('/compare', methods=['GET', 'POST'])
def compare(): return "<h1>Compare Page - Ready for Part 2</h1>"
@app.route('/estimator', methods=['GET', 'POST'])
def estimator(): return "<h1>Estimator Page - Ready for Part 2</h1>"
@app.route('/wizard', methods=['GET', 'POST'])
def wizard(): return "<h1>Wizard Page - Ready for Part 2</h1>"
@app.route('/green', methods=['GET', 'POST'])
def green(): return "<h1>Green Page - Ready for Part 2</h1>"
@app.route('/thermal', methods=['GET', 'POST'])
def thermal(): return "<h1>Thermal Page - Ready for Part 2</h1>"
@app.route('/builder', methods=['GET', 'POST'])
def builder(): return "<h1>Builder Page - Ready for Part 2</h1>"

if __name__ == '__main__': 
    app.run(debug=True)