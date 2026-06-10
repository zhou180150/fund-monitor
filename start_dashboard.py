import subprocess, os, time, sys

# 清理旧进程
subprocess.run('taskkill /F /IM python.exe 2>nul', shell=True, capture_output=True)
time.sleep(2)

# 当前 python 又活了
env = {k:v for k,v in os.environ.items() if k not in ('HTTP_PROXY','HTTPS_PROXY','http_proxy','https_proxy')}
env['STREAMLIT_EMAIL'] = ''
env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
env['NO_PROXY'] = 'localhost,127.0.0.1'

proc = subprocess.Popen(
    [sys.executable, '-m', 'streamlit', 'run', 'D:/fund_monitor/app.py',
     '--server.port', '8570'],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    env=env
)
print('PID:', proc.pid)
time.sleep(30)

import requests
r = requests.get('http://127.0.0.1:8570/', timeout=15, proxies={'http':None,'https':None})
print(r.status_code, len(r.text))
