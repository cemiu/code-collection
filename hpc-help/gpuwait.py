#!/usr/bin/env python3

"""
For Sun Grid Engine, print all GPU jobs currently waiting for execution
"""

import subprocess
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from tabulate import tabulate

cmd = "qstat -u \"*\" -s p -r -xml | xmllint --xpath '//job_list[hard_request[@name=\"gpu\"]]' -"
xml_string = subprocess.check_output(cmd, shell=True).decode()

root = ET.fromstring(f"<root>{xml_string}</root>")

data = []
for job_list in root.findall('job_list'):
    row = {}
    for child in job_list:
        if child.tag == "hard_request":
            name = child.attrib['name']
            value = child.text
            row[name] = value
        else:
            row[child.tag] = child.text
    data.append(row)

df = pd.DataFrame(data)
df = df.drop(['queue_name', 'JB_name', 'def_hard_request', 'binding', 'predecessor_jobs', 'predecessor_jobs_req', 'state', 'full_job_name', 'snx', 'batch', 'exc', 'exz', 'exy', 'master_hard_req_queue', 'exw', 'tasks', 'exx'], axis=1, errors='ignore')

df['h_rt'] = pd.to_numeric(df['h_rt'], errors='coerce')
# df['h_rt'] = pd.to_timedelta(df['h_rt'], unit='s').dt.components.iloc[:, :2].apply(lambda x: f"{x[0]}h{x[1]:02d}", axis=1)
df['h_rt'] = (pd.to_timedelta(df['h_rt'].astype(int), unit='s')
              .apply(lambda x: f"{int(x.total_seconds() // 3600)}h{(x.seconds // 60) % 60:02d}"))

current_time = datetime.now()
df['JB_submission_time'] = current_time - pd.to_datetime(df['JB_submission_time'])

def format_duration(duration):
  total_seconds = duration.total_seconds()
  hours = int(total_seconds // 3600)
  minutes = int((total_seconds % 3600) // 60)

  if hours > 0:
    return f"{hours}hours {minutes}min"
  else:
    return f"{minutes}min"

df['JB_submission_time'] = df['JB_submission_time'].apply(format_duration)

df = df.rename(columns={
    'JB_job_number': 'job_num',
    'JAT_prio': 'prio',
    'JB_owner': 'user',
    'JB_submission_time': 'submitted',
    'requested_pe': '?',
    'tmpfs': 'ssd',
    'h_rt': 'runtime',
})

df = df[df['job_num'] != '929519']
df = df.drop(['?'], axis=1, errors='ignore')

print()
print('GPU jobs waiting:')
print(tabulate(df, headers='keys', showindex=False))

