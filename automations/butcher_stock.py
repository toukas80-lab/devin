"""Εβδομαδιαία ενημέρωση butcherequip.gr από απόθεμα 3000 (μέσω /admin/stock.csv της πύλης B2B).
publish + απόθεμα<=0 -> draft (σημάδι meta _auto_stock_draft). draft με σημάδι + απόθεμα>0 -> publish.
Μόνο είδη των ομάδων GROUPS (MTRGROUP), εκτός κατασκευαστών EXCLUDE_MANUF. Χειροκίνητα drafts (χωρίς σημάδι) δεν αγγίζονται. Χρήση: python3 butcher_stock.py [--apply]"""
import csv, io, json, os, re, sys, time, datetime as dt
import requests

APPLY = '--apply' in sys.argv
MAX_CHANGES = 40
MAX_AGE_H = 36
EXCLUDE_MANUF = {'EIKASO', 'CRAZYSOUVLE'}
GROUPS = {int(x) for x in '''100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,145,146,147,149,150,151,153,154,155,156,157,158,160,161,162,163,164,165,166,167,168,169,176,180,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211'''.split(',')}
OUT = os.environ.get('OUT_DIR', '.')

def portal_stock():
    s, b = requests.Session(), 'https://b2bfountoukas.gr'
    html = s.get(b + '/admin/login', timeout=30).text
    csrf = re.search(r'name="csrf" value="([^"]+)"', html).group(1)
    r = s.post(b + '/admin/login', data={'csrf': csrf, 'pass': os.environ['B2B_ADMIN_PASSWORD']}, timeout=30, allow_redirects=False)
    if r.status_code != 303 or not r.headers.get('Location', '').endswith('/admin'):
        sys.exit('B2B admin login failed (μην ξαναδοκιμάσεις: lockout)')
    r = s.get(b + '/admin/stock.csv', timeout=60)
    r.raise_for_status()
    at = r.headers.get('X-Items-Synced-At', '')
    stock = {row['code']: float(row['stock']) for row in csv.DictReader(io.StringIO(r.text))
             if row['group_id'] and int(row['group_id']) in GROUPS
             and row['manufacturer'].strip().upper() not in EXCLUDE_MANUF}
    known = {row['code'] for row in csv.DictReader(io.StringIO(r.text))}
    return stock, known, at

def wp_session():
    s, b = requests.Session(), 'https://butcherequip.gr'
    s.get(b + '/wp-login.php', timeout=30)
    s.post(b + '/wp-login.php', data={'log': os.environ['BUTCHEREQUIP_WP_USERNAME'], 'pwd': os.environ['BUTCHEREQUIP_WP_ADMIN_PASSWORD'],
           'wp-submit': 'Log In', 'testcookie': '1', 'redirect_to': b + '/wp-admin/'}, timeout=30, allow_redirects=False)
    nonce = s.get(b + '/wp-admin/admin-ajax.php?action=rest-nonce', timeout=30).text.strip()
    if not re.fullmatch(r'[0-9a-f]{10}', nonce):
        sys.exit('butcherequip wp-admin login failed')
    s.headers['X-WP-Nonce'] = nonce
    return s, b + '/wp-json/wc/v3'

def all_products(s, api):
    out = []
    for status in ('publish', 'draft'):
        page = 1
        while True:
            r = s.get(f'{api}/products', params={'status': status, 'per_page': 100, 'page': page}, timeout=60)
            r.raise_for_status()
            d = r.json()
            out += d
            if len(d) < 100:
                break
            page += 1
    return out

def flag(p):
    return any(m['key'] == '_auto_stock_draft' and m['value'] for m in p.get('meta_data', []))

def main():
    stock, known, at = portal_stock()
    age_h = (dt.datetime.now() - dt.datetime.strptime(at, '%Y-%m-%d %H:%M:%S')).total_seconds() / 3600 if at else 999
    # η πύλη δίνει ώρα Ελλάδας: τρέξε με TZ=Europe/Athens
    s, api = wp_session()
    prods = all_products(s, api)
    to_draft, to_pub, nostock = [], [], []
    for p in prods:
        sku = (p.get('sku') or '').strip()
        if p['status'] == 'publish' and sku not in known:
            nostock.append(p)
            continue
        if sku not in stock:
            continue
        q = stock[sku]
        if p['status'] == 'publish' and q <= 0:
            to_draft.append((p, q))
        elif p['status'] == 'draft' and flag(p) and q > 0:
            to_pub.append((p, q))
    ts = time.strftime('%Y%m%d_%H%M')
    path = os.path.join(OUT, f'butcher_stock_{ts}.csv')
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['action', 'id', 'sku', 'name', 'old_status', 'stock_3000', 'regular_price', 'sale_price'])
        for act, lst in (('draft', to_draft), ('publish', to_pub)):
            for p, q in lst:
                w.writerow([act, p['id'], p['sku'], p['name'], p['status'], q, p['regular_price'], p['sale_price']])
        for p in nostock:
            w.writerow(['no_code_in_portal', p['id'], p['sku'], p['name'], p['status'], '', p['regular_price'], p['sale_price']])
    blocked = None
    if age_h > MAX_AGE_H:
        blocked = f'απόθεμα παλιό ({at})'
    elif len(to_draft) + len(to_pub) > MAX_CHANGES:
        blocked = f'πάρα πολλές αλλαγές ({len(to_draft) + len(to_pub)} > {MAX_CHANGES})'
    done = []
    if APPLY and not blocked:
        today = time.strftime('%Y-%m-%d')
        upd = [{'id': p['id'], 'status': 'draft', 'meta_data': [{'key': '_auto_stock_draft', 'value': today}]} for p, _ in to_draft]
        upd += [{'id': p['id'], 'status': 'publish', 'meta_data': [{'key': '_auto_stock_draft', 'value': ''}]} for p, _ in to_pub]
        for i in range(0, len(upd), 50):
            r = s.post(f'{api}/products/batch', json={'update': upd[i:i + 50]}, timeout=120)
            r.raise_for_status()
            done += [x for x in r.json().get('update', []) if 'error' not in x]
    print(json.dumps({
        'synced_at': at, 'age_h': round(age_h, 1), 'apply': APPLY, 'blocked': blocked, 'csv': path,
        'products': len(prods), 'updated_ok': len(done),
        'draft': [f"{p['sku']} {p['name'][:40]} ({q:g})" for p, q in to_draft],
        'publish': [f"{p['sku']} {p['name'][:40]} ({q:g})" for p, q in to_pub],
        'no_code_in_portal': [f"{p['sku']} {p['name'][:40]}" for p in nostock],
    }, ensure_ascii=False, indent=1))

if __name__ == '__main__':
    main()
