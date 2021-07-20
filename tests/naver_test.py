from dury.crawler.naver import NaverImageCralwer


if __name__ == "__main__":
    crawler = NaverImageCralwer()

    image_urls_0, rel_keywords_0 = crawler.run_on_keyword("댕댕이", limit=100)
    image_urls_1, rel_keywords_1 = crawler.run_on_keyword("마뫄", limit=100)

    print(rel_keywords_0)
    print(rel_keywords_1)
    crawler.download_images(image_urls_0, output_dir="output/naver/댕댕이")
    crawler.download_images(image_urls_1, output_dir="output/naver/마뫄")

    print("Done")
