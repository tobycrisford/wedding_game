from flask import Flask, request, session, render_template
import sqlite3
import secrets
from contextlib import closing

from prompts import agent_initial_message

DATABASE = "conversations.db"
SECRET_FILE = "secrets.txt"
SESSION_ID_LENGTH = 10

# Create the Flask application
app = Flask(__name__)

with open(SECRET_FILE,'r') as f:
    app.secret_key = f.read()


def initialize_database() -> None:
    with closing(sqlite3.connect(DATABASE)) as db_con:
        with db_con:
            try:
                db_con.execute("SELECT session_id FROM conversations")
            except sqlite3.OperationalError:
                db_con.execute("CREATE TABLE conversations(session_id, agent_id, role, counter, msg, status)")

def query_db(query: str):

    with closing(sqlite3.connect(DATABASE)) as db_con:
        with db_con:
            # print(query)
            result = db_con.execute(query).fetchall()
            # print(result)
            return result

def get_conversation(session_id: str) -> dict[str, list[str]]:

    res = query_db(f"SELECT role, counter, msg FROM conversations WHERE session_id = '{session_id}'")
        
    output = {}
    for row in res:
        if row[0] not in output:
            output[row[0]] = []
        output[row[0]].append((row[1], row[2]))

    for role in output:
        output[role].sort(key = lambda x: x[0])
        output[role] = [msg[1] for msg in output[role]]

    return output

def is_pending(session_id: str) -> bool:

    results = query_db(f"SELECT status FROM conversations WHERE session_id = '{session_id}' AND status = 'pending'")
    return len(results) != 0

def sanitize_strings(in_str: str) -> str:

    return in_str.replace("'", "\\'")

def add_msg(session_id: str, agent_id: str, role: str, msg: str, status: str) -> None:

    if status not in ('pending', 'complete'):
        raise Exception("Status can only be 'pending' or 'complete'")
    
    with closing(sqlite3.connect(DATABASE)) as db_con:
        with db_con:
            res = db_con.execute(f"SELECT max(counter) FROM conversations WHERE session_id = '{session_id}' AND role = '{role}'")
            old_counter = res.fetchone()[0]
            if old_counter is None:
                counter = 0
            else:
                counter = old_counter[0] + 1

            db_con.execute(f"""
                INSERT INTO conversations VALUES (
                    '{session_id}',
                    '{sanitize_strings(agent_id)}',
                    '{role}',
                    {counter},
                    '{sanitize_strings(msg)}',
                    '{status}'
                )
            """)

@app.route('/myconversation', methods=['POST'])
def my_conversation():
    content = request.json

    if 'session_id' not in session:
        session['session_id'] = secrets.token_urlsafe(SESSION_ID_LENGTH)
        session['agent_id'] = content['agent_id']
        add_msg(session['session_id'], session['agent_id'], 'agent', agent_initial_message, 'complete')

    if not (session['agent_id'] == content['agent_id']):
        return {'status': 'error'}

    pending = is_pending(session['session_id'])
    
    if 'msg' in content:
        if pending:
            return {'status': 'error'}
        add_msg(session['session_id'], session['agent_id'], 'user', content['msg'], 'pending')
        pending = True

    
    result = {'status': 'complete', 'pending': pending, 'conversation': get_conversation(session['session_id'])}
    print(result)
    return result

@app.route('/chat', methods=['GET'])
def chat_page():

    return render_template("index.html")

if __name__ == '__main__':
    initialize_database()
    app.run()