import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opale_project.settings')
django.setup()

from django.contrib.auth import authenticate

def test_ldap_authentication():
    print("=== Testing LDAP Authentication backend ===")
    
    # 1. Test standard AD/LDAP authentication with Guillaume Ndono
    username = 'g.ndono'
    password = 'password123'
    
    print(f"Attempting to authenticate AD user: {username} ...")
    user = authenticate(username=username, password=password)
    
    if user:
        print(f"[SUCCESS] AD User '{username}' authenticated successfully!")
        print(f"  Name: {user.first_name} {user.last_name}")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role}")
        print(f"  Direction: {user.direction.nom} (Code: {user.direction.code})")
    else:
        print("[FAILURE] AD Authentication failed.")

    # 2. Test local fallback authentication with tech_art
    print("\nAttempting to authenticate local fallback user: tech_art ...")
    local_user = authenticate(username='tech_art', password='art_2026')
    
    if local_user:
        print(f"[SUCCESS] Local User 'tech_art' authenticated successfully!")
        print(f"  Name: {local_user.first_name} {local_user.last_name}")
        print(f"  Email: {local_user.email}")
        print(f"  Role: {local_user.role}")
        print(f"  Direction: {local_user.direction.nom} (Code: {local_user.direction.code})")
    else:
        print("[FAILURE] Local Authentication failed.")

if __name__ == '__main__':
    test_ldap_authentication()
