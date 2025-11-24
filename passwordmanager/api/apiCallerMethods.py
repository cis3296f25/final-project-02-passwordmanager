import requests

#####
# methods to call the passwordManager API
#####

BASE_URL = "http://127.0.0.1:5000"

#calls POST
def add_credential(site, username, password):
    response = requests.post(f"{BASE_URL}/add", json={
        "site": site,
        "username": username,
        "password": password
    })
    return response.json()

#calls GET
def get_credential(cred_id):
    response = requests.get(f"{BASE_URL}/get/{cred_id}")
    return response.json()

def get_all_credentials():
    response = requests.get(f"{BASE_URL}/list")
    return response.json()

#calls GET generate-password
def get_new_generated_password():
    response = requests.get(f"{BASE_URL}/get/generated-password")
    return response.json()

#calls DELETE
def delete_credential(cred_id):
    response = requests.delete(f"{BASE_URL}/delete/{cred_id}")
    return response.json()

# calls PUT to update password by credential id
def update_credential(cred_id, new_site, new_username, new_password):
    response = requests.put(f"{BASE_URL}/update", json={
        "id": cred_id,
        "site": new_site,
        "username": new_username,
        "password": new_password
    })
    return response.json()

# account endpoints
def account_create(username, master_password):
    response = requests.post(f"{BASE_URL}/account/create", json={
        "username": username,
        "master_password": master_password
    })
    return response.json()

def account_login(username, master_password):
    response = requests.post(f"{BASE_URL}/account/login", json={
        "username": username,
        "master_password": master_password
    })
    return response.json()

def account_logout():
    response = requests.post(f"{BASE_URL}/account/logout")
    return response.json()

def set_master_password(new_password):
    response = requests.put(f"{BASE_URL}/account/password", json={
        "new_password": new_password
    })
    return response.json()

def get_status():
    response = requests.get(f"{BASE_URL}/status")
    return response.json()

def check_duplicate_credential(site, username):
    response = requests.post(f"{BASE_URL}/check-duplicate", json={
        "site": site,
        "username": username
    })
    return response.json()
