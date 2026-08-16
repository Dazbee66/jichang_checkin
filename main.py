import requests, json, os, re
from urllib.parse import unquote

session = requests.session()
url = os.environ.get('URL', '').rstrip('/')
email = os.environ.get('EMAIL')
passwd = os.environ.get('PASSWD')
SCKEY = os.environ.get('SCKEY') or ''

login_page = '{}/auth/login'.format(url)
login_url = '{}/auth/login'.format(url)
check_url = '{}/user/checkin'.format(url)

header = {
    'origin': url,
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    'accept': 'application/json, text/javascript, */*; q=0.01',
}


def push(title, desp):
    if not SCKEY:
        return
    try:
        requests.post('https://sctapi.ftqq.com/{}.send'.format(SCKEY),
                      data={'title': title, 'desp': str(desp)[:500]}, timeout=10)
    except Exception:
        pass


def analyze_page(html):
    """打印登录页中与登录/加密/验证码相关的代码行，帮助定位登录机制"""
    keys = ['login', 'password', 'passwd', 'geetest', 'captcha', 'md5',
            'sha256', 'sha1', 'encrypt', 'csrf', 'token', 'checkin',
            'auth', 'ajax', 'verif']
    lines = html.splitlines()
    shown = 0
    for ln in lines:
        low = ln.lower()
        if any(k in low for k in keys) and len(ln) < 500:
            print('  HTML>', ln.strip()[:400])
            shown += 1
            if shown >= 25:
                break
    if shown == 0:
        print('  HTML> (未找到相关代码行，页面前500字符:)')
        print('  HTML>', html[:500].replace(chr(10), ' '))


try:
    print('获取登录页...')
    r0 = session.get(login_page, headers=header, timeout=20)
    print('GET 状态码:', r0.status_code)
    print('cookies:', dict(session.cookies))
    analyze_page(r0.text)

    csrf = session.cookies.get('XSRF-TOKEN', '') or ''
    try:
        csrf = unquote(csrf)
    except Exception:
        pass
    print('CSRF token:', ('已获取' if csrf else '未获取到'))
    h = dict(header)
    if csrf:
        h['X-CSRF-TOKEN'] = csrf

    print('进行登录...')
    r = session.post(login_url, headers=h,
                     data={'email': email, 'passwd': passwd}, timeout=20)
    print('登录响应:', r.text[:300].replace(chr(10), ' '))
    try:
        j = r.json()
    except Exception:
        j = {}
    if j.get('ret') == 1:
        print('登录成功:', j.get('msg'))
    else:
        print('登录失败:', j.get('msg', r.text[:200]))
        push('机场签到失败', '登录失败: ' + str(j.get('msg', r.text[:200])))
        exit(1)

    print('进行签到...')
    r2 = session.post(check_url, headers=h, timeout=20)
    print('签到响应:', r2.text[:300].replace(chr(10), ' '))
    try:
        j2 = r2.json()
    except Exception:
        j2 = {}
    msg2 = j2.get('msg') or r2.text[:200]
    print('签到结果:', msg2)
    push('机场签到', msg2)

except Exception as e:
    print('异常:', repr(e))
    push('机场签到失败', repr(e))
