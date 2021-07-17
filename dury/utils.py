import requests
from typing import Dict, Optional


def download(
    url: str, output_path: str, *,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    retry: Optional[int] = 5,
):
    res = requests.get(url, headers=headers, timeout=timeout)
    if res.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(res.content)
        return output_path
    elif retry > 0:
        return download(url, output_path, headers, timeout, retry - 1)
    else:
        raise IOError("Failed to download")
