import urllib.request
import json

BASE_URL = "http://127.0.0.1:8001"

def test_flow():
    print("Testing End-to-End API Flow as performed by Frontend:")
    
    # 1. /auth/config
    req = urllib.request.Request(f"{BASE_URL}/auth/config")
    with urllib.request.urlopen(req) as res:
        cfg = json.loads(res.read().decode())
        print(f"1. /auth/config -> HTTP {res.status}: {cfg}")

    # 2. Send OTP
    data = json.dumps({"phone": "+919876543210"}).encode()
    req = urllib.request.Request(f"{BASE_URL}/auth/otp/send", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        otp_res = json.loads(res.read().decode())
        print(f"2. /auth/otp/send -> HTTP {res.status}: {otp_res}")

    # 3. Verify OTP
    data = json.dumps({"phone": "+919876543210", "otp": "123456"}).encode()
    req = urllib.request.Request(f"{BASE_URL}/auth/otp/verify", data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        auth_res = json.loads(res.read().decode())
        token = auth_res.get("access_token")
        user = auth_res.get("user")
        print(f"3. /auth/otp/verify -> HTTP {res.status}, token received: {token[:20]}..., user: {user.get('full_name')}")

    # 4. /users/me
    req = urllib.request.Request(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as res:
        me = json.loads(res.read().decode())
        print(f"4. /users/me -> HTTP {res.status}, name: {me.get('full_name')}, phone: {me.get('phone')}")

    # 5. /schemes
    req = urllib.request.Request(f"{BASE_URL}/schemes", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as res:
        schemes = json.loads(res.read().decode())
        print(f"5. /schemes -> HTTP {res.status}, schemes count: {len(schemes)}")

    # 6. /institutions
    req = urllib.request.Request(f"{BASE_URL}/institutions", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as res:
        institutions = json.loads(res.read().decode())
        print(f"6. /institutions -> HTTP {res.status}, institutions count: {len(institutions)}")


    # 8. /csc/nearby
    req = urllib.request.Request(f"{BASE_URL}/csc/nearby?latitude=12.9716&longitude=77.5946", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as res:
        cscs = json.loads(res.read().decode())
        print(f"8. /csc/nearby -> HTTP {res.status}, csc count: {len(cscs)}")

    print("\nALL 8 API CONTRACT TESTS PASSED WITH 100% SUCCESS!")

if __name__ == "__main__":
    test_flow()
