import requests

#####
# methods to call the passwordManager API
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

def get_all_credentials():
    response = requests.get(f"{BASE_URL}/list")
    return response.json()

#calls GET generate-password
def get_new_generated_password():
    response = requests.get(f"{BASE_URL}/get/generated-password")
    return response.json()

#calls DELETE
def delete_credential(site):
    response = requests.delete(f"{BASE_URL}/delete/{site}")
    return response.json()