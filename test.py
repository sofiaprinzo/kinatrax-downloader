import requests

from config import config


def test_list_folders():
    url = f"{config.API_URL}/{config.API_PATH}/list_folders_at"
    payload = {"access_token": config.API_KEY, "path": config.LIST_PATH}
    response = requests.post(url, data=payload)

    print("\nlist_folders_at")
    print(f"endpoint: {url}")
    print(f"path: {config.LIST_PATH}")
    print(f"status code: {response.status_code}")
    print(f"response text: {response.text}")


def test_download_file():
    url = f"{config.API_URL}/{config.API_PATH}/download_this_file_v1"
    payload = {"access_token": config.API_KEY, "path": config.TEST_FILE_PATH}
    response = requests.post(url, data=payload)

    print("\ndownload_this_file_v1")
    print(f"endpoint: {url}")
    print(f"path: {config.TEST_FILE_PATH}")
    print(f"status code: {response.status_code}")
    print(f"response text: {response.text}")


if __name__ == "__main__":
    test_list_folders()
    test_download_file()
