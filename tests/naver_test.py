from dury.crawler.naver import NaverImageCralwer


if __name__ == "__main__":
    crawler = NaverImageCralwer()
    image_urls = crawler.run_on_keyword("댕댕이", limit=100)
    crawler.download_images(image_urls)
    print("Done")
