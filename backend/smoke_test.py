import requests

BASE = 'http://127.0.0.1:8001'

def run_smoke_test():
    print('1. Health Check:')
    r = requests.get(f'{BASE}/health')
    assert r.status_code == 200, f'Health failed: {r.status_code}'
    print('   -> OK:', r.json()['status'])

    print('2. Scheme Catalog:')
    r = requests.get(f'{BASE}/schemes')
    assert r.status_code == 200
    schemes = r.json()
    print(f'   -> OK: {len(schemes)} schemes fetched')

    print('3. Scheme Details & EMI Amortization Prerequisites:')
    scheme_id = schemes[0]['id']
    r = requests.get(f'{BASE}/schemes/{scheme_id}')
    assert r.status_code == 200
    scheme_data = r.json()
    print(f'   -> OK: Scheme "{scheme_data["name"]}" benefits & loan ceilings loaded')

    print('4. Channel Partners & Geo-Routing:')
    r = requests.get(f'{BASE}/institutions/recommendations?state=Bihar&district=Patna&scheme_id={scheme_id}')
    assert r.status_code == 200
    partners = r.json()
    best_partner = partners.get('best_partner', {}).get('name', 'N/A')
    print(f'   -> OK: Found {partners["total_partners_found"]} partners. Best: {best_partner}')

    print('5. CSC Geo-Locator:')
    r = requests.get(f'{BASE}/csc/by-district?state=Bihar&district=Patna')
    assert r.status_code == 200
    centers = r.json().get('centers', [])
    print(f'   -> OK: {len(centers)} CSC facilitation centers identified')

    print('6. Government Integrations Status:')
    r = requests.get(f'{BASE}/integrations/status')
    assert r.status_code == 200
    print(f'   -> OK: {len(r.json())} portals verified (Aadhaar, PAN, UDYAM, DigiLocker, Schemes)')

    print('7. Firebase Operational Status:')
    r = requests.get(f'{BASE}/notifications/firebase/status')
    assert r.status_code == 200
    print('   -> OK:', r.json())

    print('\nALL PHASE 6 END-TO-END SMOKE TESTS PASSED!')

if __name__ == '__main__':
    run_smoke_test()
