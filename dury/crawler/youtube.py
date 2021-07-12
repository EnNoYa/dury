
class YouTubeClient():
    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(
        self,
        api_key: str
    ) -> None:
        self.api_key = api_key

    def get_activities(self):
        ...

    def get_channel_banners(self):
        ...

    def get_channels(self):
        ...

    def get_comments(self):
        ...
    
    def get_guide_categories(self):
        ...

    def get_playlists(self):
        ...

    def get_thumbnails(self):
        ...

    def get_video_categories(self):
        ...

    def get_videos(self):
        ...
