from flask import Flask, request, session
import sqlite3
import secrets

DATABASE = "conversations.db"
SECRET_FILE = "secrets.txt"
SESSION_ID_LENGTH = 10

# Create the Flask application
app = Flask(__name__)

with open(SECRET_FILE,'r') as f:
    app.secret_key = f.read()

db_con = sqlite3.connect(DATABASE)
db_cursor = db_con.cursor()

def initialize_database() -> None:
    try:
        db_cursor.execute("SELECT session_id FROM conversations")
    except sqlite3.OperationalError:
        db_cursor.execute("CREATE TABLE conversations(session_id, agent_id, role, counter, msg, status)")
        db_con.commit()

def get_conversation(session_id: str) -> dict[str, list[str]]:

    res = db_cursor.execute(f"SELECT role, counter, msg FROM conversations WHERE session_id = '{session_id}' AND status = 'complete'")
    output = {}
    for row in res.fetchall():
        if row[0] not in output:
            output[row[0]] = []
        output[row[0]].append((row[1], row[2]))

    for role in output:
        output[role].sort(key = lambda x: x[0])
        output[role] = [msg[1] for msg in output[role]]

    return output

def is_pending(session_id: str) -> bool:

    res = db_cursor.execute(f"SELECT status FROM conversations WHERE session_id = '{session_id}' AND status = 'pending'")
    return res.fetchone() is not None

def sanitize_strings(str: in_str) -> str:

    return in_str.replace("'", "\\'")

def add_msg(session_id: str, agent_id: str, role: str, msg: str, status: str) -> None:

    if status not in ('pending', 'complete'):
        raise Exception("Status can only be 'pending' or 'complete'")
    
    res = db_cursor.execute(f"SELECT max(counter) FROM conversations WHERE session_id = '{session_id}' AND role = '{role}'")
    old_counter = res.fetchone()
    if old_counter is None:
        counter = 0
    else:
        counter = old_counter[0] + 1

    db_cursor.execute(f"""
        INSERT INTO conversations VALUES (
            '{session_id})',
            '{sanitize_strings(agent_id)}',
            '{role}',
            {counter},
            '{sanitize_strings(msg)}',
            '{status}'
        )
    """)

    db_con.commit()

@app.route('/myconversation', methods=['POST'])
def my_conversation():
    content = request.json

    if session['session_id'] is None:
        session['session_id'] = secrets.token_urlsafe(SESSION_ID_LENGTH)
        session['agent_id'] = content['agent_id']

    if not (session['agent_id'] == content['agent_id']):
        return {'status': 'error'}

    pending = is_pending(session['session_id'])
    
    if 'msg' in content:
        if pending:
            return {'status': 'error'}
        add_msg(session['session_id'], session['agent_id'], 'user', content['msg'], 'pending')

    return {'status': 'complete', 'pending': pending, 'conversation': get_conversation(session['session_id'])}


if __name__ == '__main__':
    initialize_database()
    app.run()