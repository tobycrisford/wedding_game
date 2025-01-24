import json

from flask import Flask, request, session, render_template
import sqlite3
import secrets
from contextlib import closing

from prompts import agents
from db_utils import sanitize_strings

with open('server_config.json', 'r') as f:
    server_config = json.load(f)

# Create the Flask application
app = Flask(__name__)
app.secret_key = server_config["COOKIE_SECRET"]


def initialize_database() -> None:
    with closing(sqlite3.connect(server_config["DATABASE"])) as db_con:
        with db_con:
            try:
                db_con.execute("SELECT session_id FROM conversations")
            except sqlite3.OperationalError:
                db_con.execute("""
                    CREATE TABLE conversations(
                        rowid INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        agent_id TEXT,
                        role TEXT,
                        msg TEXT,
                        status TEXT
                    )
                """)

def query_db(query: str):

    with closing(sqlite3.connect(server_config["DATABASE"])) as db_con:
        with db_con:
            # print(query)
            result = db_con.execute(query).fetchall()
            # print(result)
            return result

def get_conversation(session_id: str, agent_id: str) -> dict[str, list[str]]:

    res = query_db(f"SELECT role, rowid, msg FROM conversations WHERE session_id = '{session_id}' AND agent_id = '{agent_id}';")
        
    output = {}
    for row in res:
        if row[0] not in output:
            output[row[0]] = []
        output[row[0]].append((row[1], row[2]))

    for role in output:
        output[role].sort(key = lambda x: x[0])
        output[role] = [msg[1] for msg in output[role]]

    return output

def is_pending(session_id: str, agent_id: str) -> bool:

    results = query_db(f"SELECT status FROM conversations WHERE session_id = '{session_id}' AND agent_id = '{agent_id}' AND status = 'pending'")
    return len(results) != 0

def add_msg(session_id: str, agent_id: str, role: str, msg: str, status: str) -> None:
    
    if status not in ('pending', 'complete'):
        raise Exception("Status can only be 'pending' or 'complete'")
    
    with closing(sqlite3.connect(server_config["DATABASE"])) as db_con:
        with db_con:
            db_con.execute(f"""
                INSERT INTO conversations (session_id, agent_id, role, msg, status) VALUES (
                    '{session_id}',
                    '{sanitize_strings(agent_id)}',
                    '{role}',
                    '{sanitize_strings(msg)}',
                    '{status}'
                )
            """)

@app.route('/jmbwhpjsql_myconversation', methods=['POST'])
def my_conversation():
    content = request.json

    if 'session_id' not in session:
        session['session_id'] = secrets.token_urlsafe(server_config["SESSION_ID_LENGTH"])

    if content['agent_id'] not in agents:
        return {'status': 'error'}

    conversation = get_conversation(session['session_id'], content['agent_id'])
    if len(conversation) == 0:
        add_msg(session['session_id'], content['agent_id'], 'agent', agents[content['agent_id']]['agent_initial_message'], 'complete')
        conversation = get_conversation(session['session_id'], content['agent_id'])

    pending = is_pending(session['session_id'], content['agent_id'])
    
    if 'msg' in content:
        if pending:
            return {'status': 'error'}
        add_msg(session['session_id'], content['agent_id'], 'user', content['msg'], 'pending')
        pending = True
        conversation = get_conversation(session['session_id'], content['agent_id'])

    result = {'status': 'complete', 'pending': pending, 'conversation': conversation}
    return result

@app.route('/jmbwhpjsql_chat', methods=['GET'])
def chat_page():

    return render_template("index.html")

if __name__ == '__main__':
    initialize_database()
    if server_config["SSL_CERT"] is None:
        app.run(host='0.0.0.0')
    else:
        app.run(host='0.0.0.0', ssl_context = (server_config["SSL_CERT"], server_config["SSL_KEY"]))