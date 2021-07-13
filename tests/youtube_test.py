import datetime

from dury.crawler.youtube import YouTubeClient


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    api_key = os.environ.get("YOUTUBE_API_KEY")
    client = YouTubeClient(api_key)

    sample_channel_id = "UC79an6pPPWpXSR8FQNvjsEw"
    sample_date = datetime.date.today() - datetime.timedelta(days=7)
    sample_date = '2018-{:02d}-{:02d}T00:00:00Z'.format(sample_date.month, sample_date.day)

    searched_videos = client.search(channel_id=sample_channel_id, type="video", order="date", published_after=sample_date)
    sample_video_id_0 = searched_videos["items"][0]["id"]["videoId"]
    sample_video_id_1 = searched_videos["items"][0]["id"]["videoId"]

    categories = client.get_video_categories(region_code="kr")
    sample_category_id = categories["items"][0]["id"]
    activities = client.get_activities(sample_channel_id)
    channels = client.get_channels(for_username="재윤TV")
    channel = client.get_channels(id=sample_channel_id)
    videos = client.get_videos(id=f"{sample_video_id_0}, {sample_video_id_1}")

    playlists = client.get_playlists(channel_id=sample_channel_id)
    comment_threads_0 = client.get_comment_threads(video_id=sample_video_id_0)
    comment_threads_1 = client.get_comment_threads(channel_id=sample_channel_id)
    sample_comment_id_0 = comment_threads_0["items"][0]["id"]
    sample_comment_id_1 = comment_threads_0["items"][0]["id"]
    comment_threads_2 = client.get_comment_threads(id=f"{sample_comment_id_0}, {sample_comment_id_1}")
    
    comments_0 = client.get_comments(parent_id=sample_comment_id_0)
    comments_1 = client.get_comments(id=sample_comment_id_0)
    
    # guide_categories = client.get_guide_categories(region_code="kr") # not working

    username = channel["items"][0]["snippet"]["title"]
    video_url = f"https://www.youtube.com/watch?v={sample_video_id_0}"
    path = client.download(video_url, "video", filename="youtube_sample", prefix=username)
    print("Done")
