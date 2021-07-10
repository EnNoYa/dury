import requests
import re
import os
from typing import List, Optional, Union, Dict, Any

from dury.utils import distributed_download


class TwitchClient():
    PUBLIC_API_URL = "https://api.twitch.tv/helix"
    OAUTH_URL = "https://id.twitch.tv/oauth2/token"
    PLAYLISTS_URL = "https://usher.ttvnw.net/vod/{}"
    PRIVATE_API_URL = "https://gql.twitch.tv/gql"

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth = self.get_oauth()
        self.headers = {
            "Client-Id": self.client_id,
            "Authorization": self.oauth
        }

    def get_oauth(self):
        res = requests.post(self.OAUTH_URL, params={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials"
        })
        oauth = res.json()
        return f"{oauth['token_type'].capitalize()} {oauth['access_token']}"

    def get_users(self, login_names: Union[str, List[str]]):
        if isinstance(login_names, str):
            login_names = [ login_names ]

        query = f"{'&'.join(f'login={login_name}' for login_name in login_names)}" 
        users = self._create_request("users", query)["data"]
        return users

    def get_channel_information(self, broadcaster_ids: Union[str, List[str]]):
        query = f"{'&'.join(f'broadcaster_id={broadcaster_id}' for broadcaster_id in broadcaster_ids)}" 
        channel_information = self._create_request("channels", query)["data"]
        return channel_information

    def get_videos(
        self,
        user_id: str, *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = 20
    ):
        query = f"user_id={user_id}&first={first}"
        if after is not None:
            query += "&after={after}"
        if before is not None:
            query += "&before={before}"

        res = self._create_request("videos", query)
        videos = res["data"]
        pagination = res["pagination"]
        return videos, pagination

    def download_video(
        self,
        video_id: str, *,
        bitrate: Optional[str] = "720p60",
        output_dir: Optional[str] = "video",
        video_name: Optional[str] = None 
    ):
        assert bitrate in [
            '160p30', '360p30', '480p30', '720p30',
            '720p60', 'audio_only', 'chunked'
        ], "Invalid bitrate"

        os.makedirs(output_dir, exist_ok=True)

        access_token = self._get_access_token(video_id)["videoPlaybackAccessToken"]
        video_uri = self._get_video_uri(video_id, access_token, bitrate=bitrate)

        chunk_uris = self._get_chunk_uris(video_uri)

        if video_name is None:
            video_name = video_id
        out_path = os.path.join(output_dir, f"{video_name}_{bitrate}.mp4")
        status = distributed_download(chunk_uris, out_path)
        return status

    def _get_access_token(self, video_id: str):
        query = """
            {{
                videoPlaybackAccessToken(
                    id: {video_id},
                    params: {{
                        platform: "web",
                        playerBackend: "mediaplayer",
                        playerType: "site"
                    }}
                ) {{
                    signature
                    value
                }}
            }}
        """
        query = query.format(video_id=video_id)
        headers = { "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko" }
        res = requests.post(self.PRIVATE_API_URL, json={"query": query}, headers=headers)
        access_token = res.json()["data"]
        return access_token

    def _get_video_uri(
        self,
        video_id: str,
        access_token: Dict[str, Any], *,
        bitrate: Optional[str] = "720p60"
    ):
        playlists_url = self.PLAYLISTS_URL.format(video_id)
        res = requests.get(playlists_url, params={
            "nauthsig": access_token["signature"],
            "nauth": access_token["value"],
            "allow_source": "true",
            "player": "twitchweb",
            "allow_spectre": "true",
            "allow_audio_only": "true"
        })
        playlists = res.text.split("\n")
        video_uri = list(filter(lambda x: x[:5] == "https" and bitrate in x, playlists))[0]
        return video_uri

    def _get_chunk_uris(self, video_uri: str):
        res = requests.get(video_uri)
        chunk_list = res.text.split("\n")
        chunk_list = list(filter(lambda x: re.match("(\w|\d)+\.ts", x), chunk_list))

        base_url = os.path.dirname(video_uri)
        chunk_uris = [ f"{base_url}/{chunk}" for chunk in chunk_list ]
        return chunk_uris

    def _create_request(self, path: str, query: str):
        res = requests.get(
            f"{self.PUBLIC_API_URL}/{path}?{query}",
            headers=self.headers
        )
        return res.json()


class TwitchCrawler():

    def __init__(self, cfg) -> None:
        pass
