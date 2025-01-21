import sqlite3
import time

import pandas as pd
import numpy as np

from prompts import agents
from db_utils import sanitize_strings
from load_generation_pipeline import load_pipeline

DATABASE = "conversations.db"

pipe = load_pipeline()

db_con = sqlite3.connect(DATABASE)

def get_pending() -> list[tuple]:

    cols = ['session_id', 'agent_id', 'rowid', 'msg']

    with db_con:
        res = db_con.execute("SELECT " + ', '.join(cols) + " FROM conversations WHERE status = 'pending' ORDER BY rowid;")
        return pd.DataFrame(res.fetchall(), columns=cols)


def delete_row(rowid: int) -> None:

    with db_con:
        db_con.execute(f"DELETE FROM conversations WHERE rowid = {rowid}")

def clean_pending(pending_msgs: pd.DataFrame) -> pd.DataFrame:

    rows_to_keep = set()
    
    for session, df in pending_msgs.groupby(['session_id', 'agent_id']):

        df_sorted = df.sort_values('rowid')
        
        # Tidy up database if have concurrency problems - only respond to one message at a time!
        if len(df_sorted) > 1:
            for i in df_sorted.index[:-1]:
                delete_row(df_sorted.loc[i, 'rowid'])

        rows_to_keep.add(df_sorted.iloc[-1,:]['rowid'])

    return pending_msgs[pending_msgs['rowid'].isin(rows_to_keep)]

def fetch_whole_conversation(session_id: str, agent_id: str) -> list[dict[str,str]]:

    with db_con:
        conv = db_con.execute(f"""
            SELECT role, msg FROM conversations
            WHERE session_id = '{session_id}' AND agent_id = '{agent_id}'
            ORDER BY rowid
        """).fetchall()

    messages = [
        {'role': row[0], 'content': row[1]} for row in conv
    ]

    return messages


def generate_response(row: pd.Series) -> str:

    messages = [{'role': 'system', 'content': agents[row['agent_id']]['system_prompt']}]
    messages += fetch_whole_conversation(row['session_id'], row['agent_id'])

    output = pipe(messages, max_new_tokens=1024)
    response = output[0]['generated_text'][-1]['content']
    
    return response

def update_row_with_response(row: pd.Series, response: str) -> None:

    with db_con:
        db_con.execute(f"""
            INSERT INTO conversations (session_id, agent_id, role, msg, status) VALUES (
                '{row['session_id']}',
                '{row['agent_id']}',
                'agent',
                '{sanitize_strings(response)}',
                'complete'
            )
        """)

        db_con.execute(f"""
            UPDATE conversations SET status = 'complete' WHERE rowid = {row['rowid']};
        """)


if __name__ == "__main__":
    print("Listening for responses to process...")
    while True:

        pending_rows = clean_pending(get_pending())
        for idx, row in pending_rows.iterrows():
            try:
                print(f"Generating new response for {row['msg']}")
                response = generate_response(row)
                update_row_with_response(row, response)
                print("New response generated.")
            except Exception as e:
                print(f"Error with {row}: {e}")
                continue

        time.sleep(10)