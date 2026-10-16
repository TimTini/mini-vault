"""Check staged public files without printing matched secret values."""
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def staged_files():
    output=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT)
    return [p for p in output.decode('utf-8').split('\0') if p]

def check():
    patterns={
        'private_key':r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----',
        'github_token':r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,})\b',
        'cloud_access_key':r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
        'credential_assignment':r'''(?im)^\s*["']?(?:api_key|api_secret|password|access_token|refresh_token|client_secret)["']?\s*[:=]\s*["'][^"'\s]{8,}["']''',
        'personal_profile_path':r'(?i)\b[A-Z]:[\\/]Users[\\/][^\s\\/"<>]+',
        'machine_drive_path':r'(?<![A-Za-z])[A-Za-z]:[\\/](?!/)',
        'email':r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
    }
    findings=[];files=staged_files();size=0
    for name in files:
        data=subprocess.check_output(['git','show',':'+name],cwd=ROOT)
        size+=len(data)
        if len(data)>95*1024*1024:findings.append(dict(file=name,category='oversized_git_blob'))
        if Path(name).suffix.lower() in ['.png','.jpg','.jpeg']:continue
        try:text=data.decode('utf-8-sig')
        except UnicodeDecodeError:
            findings.append(dict(file=name,category='unreviewed_binary'));continue
        for category,pattern in patterns.items():
            for match in re.finditer(pattern,text):
                # The bundled dependency preserves the public copyright contact.
                if category=='email' and name=='simulator/vendor/THREE-LICENSE.txt':continue
                # Regex definitions are scanner code, not credential values.
                if name=='work/publication-audit.py':continue
                findings.append(dict(file=name,line=text.count('\n',0,match.start())+1,category=category))
    ignored=['.env','simulator/.env','work/environment.json','work/mini-vault-progress.md',
             'work/backup/private.txt','exports/mini-vault-200-scale-1-print.stl','reference/MINI-VAULT.stl',
             'simulator/credentials.json','simulator/private.key','tests/__pycache__/x.pyc']
    for name in ignored:
        result=subprocess.run(['git','check-ignore','-q','--no-index',name],cwd=ROOT)
        if result.returncode:findings.append(dict(file=name,category='ignore_rule_missing'))
    report=dict(scope='Git index only; pattern checks plus explicitly reviewed source/rendered images; not a universal secret detector',
                tracked_files=len(files),staged_bytes=size,ignore_probes=len(ignored),findings=findings)
    target=ROOT/'work/publication/privacy-audit.json'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))
    return 1 if findings else 0

if __name__=='__main__':raise SystemExit(check())
