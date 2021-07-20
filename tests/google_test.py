from dury.crawler.google import GoogleImageCralwer


if __name__ == "__main__":
    crawler = GoogleImageCralwer()
    image_urls = crawler.run_on_keyword("망나뇽", limit=10)
    crawler.download_images(image_urls)
    print("Done")
