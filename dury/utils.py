import requests

def download_image(url, out_path, headers={}, timeout=10):
    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        if res.status_code != 200:
            return IOError("Failed request")
        with open(out_path, "wb") as f:
            f.write(res.content)
    except Exception as e:
        return e
    return 0
