import requests, json, os
from urllib.parse import unquote

session = requests.session()
# 机场的地址
url = os.environ.get('URL', '').rstrip('/')
# 配置用户名（一般是邮箱）
email = os.environ.get('EMAIL')
# 配置用户名对应的密码 和上面的email对应上
passwd = os.environ.get('PASSWD')
# server酱
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
        print('推送成功')
    except Exception as e:
        print('推送失败:', repr(e))


try:
    # 1) 先 GET 登录页，获取 session cookie（含 CSRF）
    print('获取登录页...')
    r0 = session.get(login_page, headers=header, timeout=20)
    print('GET /auth/login 状态码:', r0.status_code)
    snippet = r0.text[:200].replace(chr(10), ' ')
    print('GET 响应前200字符:', snippet)
    print('cookies:', dict(session.cookies))

    # 2) 从 cookie 提取 XSRF-TOKEN 作为 CSRF
    csrf = session.cookies.get('XSRF-TOKEN', '') or ''
    try:
        csrf = unquote(csrf)
    except Exception:
        pass
    print('CSRF token:', ('已获取' if csrf else '未获取到'))
    h = dict(header)
    if csrf:
        h['X-CSRF-TOKEN'] = csrf

    # 3) 登录
    print('进行登录...')
    r = session.post(login_url, headers=h,
                     data={'email': email, 'passwd': passwd}, timeout=20)
    try:
        j = r.json()
    except Exception:
        j = {}
        print('登录响应非JSON, 前200字符:', r.text[:200].replace(chr(10), ' '))
    if j.get('ret') == 1:
        print('登录成功:', j.get('msg'))
    else:
        msg = j.get('msg') or r.text[:200]
        print('登录失败:', msg)
        push('机场签到失败', '登录失败: ' + str(msg))
        exit(1)

    # 4) 签到
    print('进行签到...')
    r2 = session.post(check_url, headers=h, timeout=20)
    try:
        j2 = r2.json()
    except Exception:
        j2 = {}
        print('签到响应非JSON, 前200字符:', r2.text[:200].replace(chr(10), ' '))
    msg2 = j2.get('msg') or r2.text[:200]
    print('签到结果:', msg2)
    push('机场签到', msg2)

except Exception as e:
    print('异常:', repr(e))
    push('机场签到失败', repr(e))
