import subprocess, re
paths = [
    r'HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon',
    r'HKEY_LOCAL_MACHINE\SOFTWARE\Google\Chrome\BLBeacon',
    r'HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Google\Chrome\BLBeacon',
]
for path in paths:
    try:
        out = subprocess.check_output(f'reg query "{path}" /v version', shell=True, stderr=subprocess.DEVNULL).decode()
        m = re.search(r'version\s+REG_SZ\s+([\d.]+)', out)
        if m:
            print(f'Chrome version: {m.group(1)} -> major: {m.group(1).split(".")[0]}')
            break
    except:
        pass
else:
    print('Chrome version not found in registry')
