#!/usr/bin/env python3

"""
For Sun Grid Engine, print all GPU nodes' utilizations
"""

import subprocess
import xml.etree.ElementTree as ET
import pandas as pd
from tabulate import tabulate

xml_output = subprocess.run(['qstat', '-u', '*', '-s', 'r', '-r', '-l', 'gpu', '-xml'], capture_output=True, text=True).stdout
root = ET.fromstring(xml_output)
node_data = {}

for job in root.findall('.//job_list'):
    queue_name = job.find('queue_name').text
    node_name = queue_name.split('@')[1].split('.')[0]
    cpus = int(job.find('slots').text)
    job_id = job.find('JB_job_number').text
    hard_requests = {}
    for req in job.findall('hard_request'):
        name = req.get('name')
        value = req.text
        if name in ['batch', 'h_rt', 'exx', 'threads']:
            continue
        if name in ['tmpfs', 'memory']:
            value = int(float(value[:-1]) * (1024 if value.endswith('G') else 1))
        elif name in ['gpu', 'snx']:
            value = int(value)
        hard_requests[name] = value
    node_data.setdefault(node_name, {'cpus': 0, 'jobs': 0, 'job_list': [], 'hard_requests': {}})
    node_data[node_name]['cpus'] += cpus
    node_data[node_name]['jobs'] += 1
    node_data[node_name]['job_list'].append(job_id)
    for name, value in hard_requests.items():
        node_data[node_name]['hard_requests'].setdefault(name, 0)
        try:
            node_data[node_name]['hard_requests'][name] += value
        except TypeError:
            pass 

rows = []
for node_name, data in node_data.items():
    cpus = data['cpus']
    memory = data['hard_requests'].get('memory', 0)
    data['hard_requests']['cpus * memory'] = cpus * memory
    row = {
        'node': node_name,
        'jobs': data['jobs'],
        'cpus': cpus,
        'job_list': ','.join(data['job_list'])
    }
    for name, value in data['hard_requests'].items():
        if name not in ['snx']:
            if name == 'memory':
                row['mem/cpu'] = f"{value / 1024:.2f}G" if cpus else "N/A"
            elif name == 'cpus * memory':
                row['mem'] = f"{value / 1024:.2f}G"
            elif name == 'tmpfs':
                row['ssd'] = f"{value / 1024:.2f}G"
            elif name == 'gpu':
                row['gpus'] = value
            else:
                row[name] = value
    row['interactive'] = not pd.isna(row.get('interactive', float('nan')))
    rows.append(row)

df = pd.DataFrame(rows)
df = df[['node', 'jobs', 'gpus', 'cpus', 'mem', 'ssd', 'mem/cpu', 'interactive', 'job_list']]
df['is_64_cpu'] = df['cpus'] == 64
df = df.sort_values(by=['is_64_cpu', 'gpus', 'mem'], ascending=[True, True, True])
df = df.drop('is_64_cpu', axis=1)

interactive_count = (df['interactive'] == True).sum()
non_interactive_count = (df['interactive'] == False).sum()

n = sum((df['cpus'] == 64) | (df['gpus'] == 8))
df_str = []
for i in range(len(df)):
    row = df.iloc[i]
    if (row['cpus'] == 64 or row['gpus'] == 8) and i >= len(df) - n:
        row_str = [f"\033[90m{val}\033[0m" for val in row.values]
    else:
        row_str = row.values.astype(str)
    df_str.append(row_str)

print()
print('GPU nodes util:')
print(tabulate(df_str, headers=df.columns))

if interactive_count < 5:
    print("\033[91mInteractive node free\033[0m")
if non_interactive_count < 1:
    print("\033[91mNon-interactive node available\033[0m")

