from dury.crawler.twitch import TwitchClient


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()

    client_id = os.environ.get("TWITCH_CLIENT_ID")
    client_secret = os.environ.get("TWITCH_CLIENT_SECRET")

    client = TwitchClient(client_id, client_secret)

    login_ids = ["ddahyoni", "pjs9073", "leechunhyang"]
    users = client.get_users(login=login_ids)
    user_ids = [user["id"] for user in users["data"]]
    user_follows = client.get_user_follows(to_id=user_ids[2])
    channel_information = client.get_channel_information(user_ids)
    channel_emotes = client.get_channel_emotes(user_ids[0])
    channel_chat_badges = client.get_channel_chat_badges(user_ids[0])
    clips = client.get_clips(user_ids[0])
    top_games = client.get_top_games(first=20)
    game_ids = [top_game["id"] for top_game in top_games["data"]]
    games = client.get_games(game_ids)
    streams = client.get_streams(user_login=login_ids)
    all_stream_tags = client.get_all_stream_tags()
    stream_tags = client.get_stream_tags(user_ids[0])
    channel_teams = client.get_channel_teams(user_ids)
    teams = client.get_teams(team_name=channel_teams["data"][0]["team_name"])
    videos = client.get_videos(user_ids[0], first=20)
    video_id = "1068131366"
    status = client.download_video(video_id, video_name="test", bitrate="160p30")

    print("Done")
