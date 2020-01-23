#!/usr/bin/env python

import requests, io, subprocess, time, zipfile
from bs4 import BeautifulSoup as Soup

password_path = '/etc/openvpn/password.txt'
config_path = '/etc/openvpn/hideme.conf'

ocr_uri = 'https://api.ocr.space/parse/image'
api_key = '5a64d478-9c89-43d8-88e3-c65de9999580'

base = 'https://www.vpnbook.com'
username = 'vpnbook'

def select_entry(entry_type, entries, labels):
    print('Select', entry_type, 'from below [0]')
    for i, label in enumerate(labels):
        print(f'[{i}] {label}')
    try:
        i = input() or 0
        return entries[int(i)]
    except:
        print(f'Invalid option ({i})')
        exit()


print('Getting VPN password...')
try:
    s = requests.Session()
    r = s.get(base)
    soup = Soup(r.text, 'html.parser')

    img_src = next(filter(lambda img: img['src'].startswith('password'), soup.findAll('img')))['src']
    params = {'url': f'{base}/{img_src}'}
    headers = {'apikey': api_key}
    response = requests.post(ocr_uri, params, headers=headers)
    password = response.json()['ParsedResults'][0]['ParsedText'].strip()

    with open(password_path, 'w') as file:
        file.write('\n'.join((username, password)))
except:
    print(f'Cannot find password, write it yourself in `{password_path}`')
print()

try:
    links = list(filter(lambda a: a['href'].endswith('.zip'), soup.findAll('a')))
    labels = map(lambda a: a.text, links)
    ref = select_entry('a VPN server', links, labels)['href']
    profile_url = base + ref
except:
    print('Cannot get VPN server list')
    exit()
print()

try:
    req = requests.get(profile_url, stream=True)
    zf = zipfile.ZipFile(io.BytesIO(req.content))
    entry = select_entry('a profile', zf.filelist, zf.namelist())
    with open(config_path, 'wb') as file:
        file.write(zf.read(entry))
except:
    print('Cannot get ovpn profile')
    raise
    exit()
print()

print('Launching VPN...')
p = subprocess.Popen(['sudo', 'openvpn', '--config', config_path, '--auth-user-pass', password_path])

#http://askubuntu.com/questions/298419/how-to-disconnect-from-openvpn
print('\nVPN Started - To kill openvpn run "sudo killall openvpn"\n')
print('Termination with Ctrl+C\n')

try:
    while True:
        time.sleep(600)
# termination with Ctrl+C
except:
    try:
        p.kill()
    except:
        pass
    while p.poll() != 0:
        time.sleep(1)
    print('\nVPN terminated')

exit()
