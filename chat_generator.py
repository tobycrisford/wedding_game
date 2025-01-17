import sqlite3
import time

import pandas as pd
import numpy as np

from db_utils import sanitize_strings

DATABASE = "conversations.db"

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
    
    for session, df in pending_msgs.groupby('session_id'):

        df_sorted = df.sort_values('rowid')
        
        # Tidy up database if have concurrency problems - only respond to one message at a time!
        if len(df_sorted) > 1:
            for i in df_sorted.index[:-1]:
                delete_row(df_sorted.loc[i, 'rowid'])

        rows_to_keep.add(df_sorted.iloc[-1,:]['rowid'])

    return pending_msgs[pending_msgs['rowid'].isin(rows_to_keep)]


def generate_response(row: pd.Series) -> str:

    return np.random.choice(['Hmm...', 'Hello there', 'I am the globglogabgalab'])

def update_row_with_response(row: pd.Series, response: str) -> None:

    with db_con:
        db_con.execute(f"""
            INSERT INTO conversations VALUES (
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


while True:

    pending_rows = clean_pending(get_pending())
    for idx, row in pending_rows.iterrows():
        response = generate_response(row)
        update_row_with_response(row, response)

    time.sleep(10)