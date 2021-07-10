import time
import os
import shutil
import requests
from multiprocessing.pool import ThreadPool
from typing import List, Dict, Optional


def download(
    url: str, out_path: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None
):
    try:
        res = requests.get(url, headers=headers, timeout=timeout)
        if res.status_code != 200:
            return IOError("Failed request")
        with open(out_path, "wb") as f:
            f.write(res.content)
        return 0
    except Exception as e:
        return -1


def distributed_download(
    urls: List[str],
    out_path: str, *,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[int] = None,
    num_thread: Optional[int] = 5
) -> int:
    try:
        timestamp = int(time.time())
        tmp_dir = os.path.join("/tmp", "dury", str(timestamp))
        os.makedirs(tmp_dir, exist_ok=True)
        urls = [ (str(i), url) for i, url in enumerate(urls) ]
        
        task = lambda x: download(
            x[1],
            os.path.join(tmp_dir, f"{x[0].zfill(8)}.ts"),
            headers=headers,
            timeout=timeout
        )
        thread_pool = ThreadPool(num_thread)
        thread_pool.map(task, urls)

        merge_chunks(tmp_dir, out_path)
        return 0
    except Exception as e:
        return -1
    finally:
        shutil.rmtree(tmp_dir)


def merge_chunks(chunk_dir: str, out_path: str) -> None:
    chunk_list = os.listdir(chunk_dir)
    chunk_list.sort(key=lambda x: int(x.split(".")[0]))

    with open(out_path, "wb") as f:
        for chunk_name in chunk_list:
            chunk_path = os.path.join(chunk_dir, chunk_name)
            with open(chunk_path, "rb") as chunk:
                f.write(chunk.read())
