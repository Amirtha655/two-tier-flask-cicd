import os
import pymysql
from flask import Flask, render_template, request, jsonify
import time

app = Flask(__name__)

def get_db():
    return pymysql.connect(
        host=os.environ.get('MYSQL_HOST', 'localhost'),
        user=os.environ.get('MYSQL_USER', 'root'),
        password=os.environ.get('MYSQL_PASSWORD', 'root'),
        database=os.environ.get('MYSQL_DB', 'devops'),
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    for attempt in range(15):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute('CREATE TABLE IF NOT EXISTS messages (id INT AUTO_INCREMENT PRIMARY KEY, message TEXT);')
            conn.commit()
            cur.close()
            conn.close()
            print("Database initialized.")
            return
        except pymysql.err.OperationalError as e:
            print(f"MySQL not ready ({attempt+1}/15): {e}")
            time.sleep(4)
    raise Exception("Could not connect to MySQL after retries")


@app.route('/')
def hello():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT message FROM messages')
    messages = [row['message'] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return render_template('index.html', messages=messages)

@app.route('/submit', methods=['POST'])
def submit():
    new_message = request.form.get('new_message')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO messages (message) VALUES (%s)', [new_message])
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': new_message})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
