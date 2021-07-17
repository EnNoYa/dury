import requests
import re
import os
import time
from concurrent.futures import ThreadPoolExecutor
import shutil
from typing import List, Optional, Union, Dict, Any

from tqdm import tqdm
from loguru import logger

from .base import APIWrapper
from dury.utils import download


class TwitchClient(APIWrapper):
    PUBLIC_API_URL = "https://api.twitch.tv/helix"
    OAUTH_URL = "https://id.twitch.tv/oauth2/token"
    PLAYLISTS_URL = "https://usher.ttvnw.net/vod/{}"
    PRIVATE_API_URL = "https://gql.twitch.tv/gql"

    def __init__(self, client_id: str, client_secret: str) -> None:
        self.__client_id = client_id
        self.__client_secret = client_secret
        self.__oauth = self.get_oauth(self.__client_id, self.__client_secret)

        super(TwitchClient, self).__init__(
            self.PUBLIC_API_URL,
            headers={
                "Client-Id": self.__client_id,
                "Authorization": self.__oauth
            }
        )

    def get_oauth(self, client_id: str, client_secret: str):
        res = requests.post(self.OAUTH_URL, params={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        })
        oauth = res.json()
        return f"{oauth['token_type'].capitalize()} {oauth['access_token']}"

    def get_users(
        self, *,
        id: Optional[Union[str, List[str]]] = None,
        login: Optional[Union[str, List[str]]] = None
    ):
        params = { "id": id, "login": login }
        return self._get("users", params=params)

    def get_user_follows(
        self, *,
        after: Optional[str] = None,
        first:  Optional[int] = 20,
        from_id: Optional[str] = None,
        to_id: Optional[str] = None,
    ):
        params = {
            "from_id": from_id, "to_id": to_id,
            "first": first, "after": after
        }
        return self._get("users/follows", params=params)

    def get_channel_information(self, broadcaster_id: Union[str, List[str]]):
        params = { "broadcaster_id": broadcaster_id }
        return self._get("channels", params=params)

    def get_channel_emotes(self, broadcaster_id: str):
        params = { "broadcaster_id": broadcaster_id }
        return self._get("chat/emotes", params=params)

    def get_channel_chat_badges(self, broadcaster_id: str):
        params = { "broadcaster_id": broadcaster_id }
        return self._get("chat/badges", params=params)

    def get_clips(
        self,
        broadcaster_id: str, *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = 20
    ):
        params = {
            "broadcaster_id": broadcaster_id, "first": first,
            "after": after, "before": before
        }
        return self._get("clips", params=params)
    
    def get_top_games(self, *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = 20
    ):
        params = { "first": first, "after": after, "before": before }
        return self._get("games/top", params=params)


    def get_games(self, game_id: Union[str, List[str]]):
        params = { "id": game_id }
        return self._get("games", params=params)

    def get_streams(
        self, *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = 20,
        game_id: Optional[Union[str, List[str]]] = None,
        user_id: Optional[Union[str, List[str]]] = None,
        user_login: Optional[Union[str, List[str]]] = None,
    ):
        params = {
            "game_id": game_id, "user_id": user_id,
            "user_login": user_login, "first": first,
            "after": after, "before": before
        }
        return self._get("streams", params=params)

    def get_all_stream_tags(
        self, *,
        after: Optional[str] = None,
        first: Optional[int] = 20,
        tag_id: Optional[Union[str, List[str]]] = None
    ):
        params = { "tag_id": tag_id, "first": first, "after": after }
        return self._get("tags/streams", params=params)

    def get_stream_tags(self, broadcaster_id: str):
        params = { "broadcaster_id": broadcaster_id }
        return self._get("streams/tags", params=params)

    def get_channel_teams(self, broadcaster_id: Union[str, List[str]]):
        params = { "broadcaster_id": broadcaster_id }
        return self._get("teams/channel", params=params)

    def get_teams(
        self, *,
        team_name: Optional[str] = None,
        team_id: Optional[str] = None
    ):
        params = { "name": team_name, "id": team_id }
        return self._get("teams", params=params)

    def get_videos(
        self,
        user_id: str, *,
        after: Optional[str] = None,
        before: Optional[str] = None,
        first: Optional[int] = 20
    ):
        params = {
            "user_id": user_id, "first": first,
            "after": after, "before": before
        }
        return self._get("videos", params=params)

    def download_video(
        self,
        video_id: str, *,
        bitrate: Optional[str] = "720p60",
        output_dir: Optional[str] = "twitch/video",
        video_name: Optional[str] = None,
        num_workers: Optional[int] = 10,
        retry: Optional[int] = 5
    ):
        assert bitrate in [
            '160p30', '360p30', '480p30', '720p30',
            '720p60', 'audio_only', 'chunked'
        ], "Invalid bitrate"

        access_token = self._get_access_token(video_id)["data"]["videoPlaybackAccessToken"]
        video_uri = self._get_video_uri(video_id, access_token, bitrate=bitrate)
        chunk_uris = self._get_chunk_uris(video_uri)

        timestamp = int(time.time())
        tmp_dir = os.path.join("/tmp", "dury", str(timestamp))
        os.makedirs(tmp_dir, exist_ok=True)
        task = lambda x: download(x[1], os.path.join(tmp_dir, f"{str(x[0]).zfill(8)}.ts"), retry=retry)

        try:
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                results = list(tqdm(executor.map(task, enumerate(chunk_uris)), total=len(chunk_uris)))

            os.makedirs(output_dir, exist_ok=True)
            if video_name is None:
                video_name = video_id

            video_path = os.path.join(output_dir, f"{video_name}_{bitrate}.mp4")
            output_path = self._merge_chunks(results, video_path)
            return output_path
        except Exception as e:
            logger.error(e)
            return None
        finally:
            shutil.rmtree(tmp_dir)

    def _merge_chunks(self, chunk_list: List[str], output_path: str):
        chunk_list.sort(key=lambda x: int(os.path.basename(x).split(".")[0]))

        with open(output_path, "wb") as f:
            for chunk_path in chunk_list:
                with open(chunk_path, "rb") as chunk:
                    f.write(chunk.read())
        return output_path

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
        return res.json()

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
