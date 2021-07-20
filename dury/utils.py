import requests
from typing import Dict, Optional


DEFAULT_HEADER =  { "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36" }


def download(
    url: str, output_path: str, *,
    headers: Optional[Dict[str, str]] = DEFAULT_HEADER,
    timeout: Optional[int] = None,
    retry: Optional[int] = 5,
):
    res = requests.get(url, headers=headers, timeout=timeout)
    if res.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(res.content)
        return output_path
    elif retry > 0:
        return download(url, output_path, headers=headers, timeout=timeout, retry=retry - 1)
    else:
        raise IOError("Failed to download")
