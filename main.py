import requests
from gui import MainWindow

#####
# Skeleton for what will eventually be the GUI. For now, makes basic calls 
# to the API (assuming it's already running on http://127.0.0.1:5000)
#####

BASE_URL = "http://127.0.0.1:5000"
BASE_ROUTE = "credentials"

#calls POST
def add_credential(site, username, password):
    response = requests.post(f"{BASE_URL}/add", json={
        "site": site,
        "username": username,
        "password": password
    })
    return response.json()

#calls GET
def get_credential(site):
    response = requests.get(f"{BASE_URL}/get/{site}")
    return response.json()

#calls GET generate-password
def get_new_generated_password():
    response = requests.get(f"{BASE_URL}/get/generated-password")
    return response.json()

#calls DELETE
def delete_credential(site):
    response = requests.delete(f"{BASE_URL}/delete/{site}")
    return response.json()

if __name__ == "__main__":
    MainWindow = MainWindow()
    test_site = "example.com"
    test_user = "alice"
    test_pass = get_new_generated_password()
    test_pass = test_pass["password"]
    print(f"Generated password: {test_pass}")

    print(f"Adding credential for {test_user}@{test_site}")
    print(add_credential(test_site, test_user, test_pass))

    print(f"\nRetrieving credential for {test_site}")
    print(get_credential(test_site))

    print(f"\nDeleting credential for {test_site}")
    print(delete_credential(test_site))

    print(f"\nChecking if {test_site} still exists")
    print(get_credential(test_site))
