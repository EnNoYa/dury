from dury.crawler.instagram import InstagramClient


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()

    access_token = os.environ.get("FACEBOOK_ACCESS_TOKEN")
    client = InstagramClient(access_token)
    print("Done")
