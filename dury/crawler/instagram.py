from .base import APIWrapper


class InstagramClient(APIWrapper):
    PUBLIC_API_URL = "https://graph.facebook.com"

    def __init__(self, access_token: str) -> None:
        super(InstagramClient, self).__init__(self.PUBLIC_API_URL)
        self.access_token = access_token

    def get_user_business(self, user_id: str, username: str):
        params = {
            "access_token": self.access_token,
            # "fields": "biography, id, ig_id, followers_count, follows_count, media_count, username, name, profile_picture_url, website",
            "fields": "id"
        }
        res = self._get(user_id, params=params)
        return res
