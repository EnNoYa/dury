from dury.crawler.google import GoogleImageCralwer


if __name__ == "__main__":
    crawler = GoogleImageCralwer()
    image_urls_1, rel_keywords_0 = crawler.run_on_keyword("망나뇽", limit=10)
    image_urls_0, rel_keywords_1 = crawler.run_on_keyword("마뫄", limit=10)
    
    print(rel_keywords_0)
    print(rel_keywords_1)
    crawler.download_images(image_urls_0, output_dir="output/google/댕댕이")
    crawler.download_images(image_urls_1, output_dir="output/google/마뫄")

    print("Done")
