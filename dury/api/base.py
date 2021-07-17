import requests
from typing import Optional, Dict, Any

class APIWrapper:
    def __init__(
        self,
        base_url: str, *,
        headers: Optional[Dict[str, Any]] = None
    ) -> None:
        self._base_url = base_url
        self._headers = headers

    def _get(
        self,
        path: str, *,
        params: Optional[Dict[str, Any]] = None
    ):
        res = requests.get(
            f"{self._base_url}/{path}",
            params=params,
            headers=self._headers
        )
        return res.json()

    def _post(self):
        ...

    def _put(self):
        ...
    
    def _delete(self):
        ...