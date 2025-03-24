'''Script to turn a csv dump of conversations database into jsons, for static replay
of conversations that happened on the day.
'''

import json

import pandas as pd

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



conv_dump = pd.read_csv('conversation_dump.csv')
conv_dump.columns = ['rowid','session_id','agent_id','role','msg','status']

conv_ids = conv_dump['session_id'].unique()
all_convs = {}
for conv_id in conv_ids:
    conversation = conv_dump.loc[conv_dump['session_id'] == conv_id, ['role','rowid','msg']]

    output = {}
    for _, row in conversation.iterrows():
        if row['role'] not in output:
            output[row['role']] = []
        output[row['role']].append((row['rowid'], row['msg']))

    for role in output:
        output[role].sort(key = lambda x: x[0])
        output[role] = [msg[1] for msg in output[role]]

    all_convs[conv_id] = {'status': 'complete', 'pending': False, 'conversation': output}


with open('conversation_dump.json', 'w') as f:
    json.dump(all_convs, f)

    