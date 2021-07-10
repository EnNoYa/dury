from dury.crawler.pixiv import PixivCrawler


if __name__ == "__main__":
    import argparse
    from dury.config import get_default_config

    parser = argparse.ArgumentParser()
    parser.add_argument("--config-file", required=True)
    parser.add_argument("--mode", choices=["author", "keyword"], required=True)
    parser.add_argument("--target", type=str, required=True)
    args = parser.parse_args()

    cfg = get_default_config()
    cfg.merge_from_file(args.config_file)
    cfg.freeze()

    crawler = PixivCrawler(cfg)

    crawler.run(args.target, args.mode, cfg.OUTPUT_DIR)
    print("Done")
