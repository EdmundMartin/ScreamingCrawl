import argparse
from crawl import Crawl
from multiprocessing import freeze_support


def wrap_crawl(url, threads, user_agent, proxy, timeout, obey_robots, max_urls, data_format):
    freeze_support()
    seo = Crawl(url, threads=threads, user_agent=user_agent, proxy=proxy, timeout=timeout, obey_robots=obey_robots,
                max_urls=max_urls, data_format=data_format)
    seo.run_crawler()

parser = argparse.ArgumentParser()
parser.add_argument("url", type=str, help="url to start the crawl from")
parser.add_argument("-t", "--threads", type=int, help="number of threads - scale with caution", default=20)
parser.add_argument("-a", "--agent", type=str, help="user-agent", default="Google")
parser.add_argument("-p", "--proxy", help="proxy to use with crawler", default=None)
parser.add_argument("-o", "--timeout", type=int, help="time to stop crawl after no new urls are found", default=30)
parser.add_argument("-r", "--robots", type=bool, help="whether you obey robots.txt rules", default=True)
parser.add_argument("-m", "--max_urls", help="stop crawling after data collected from a list of urls", default=None)
parser.add_argument("-d", "--data_format", type=str, help="data format, either csv or sql", default="csv")

args = parser.parse_args()
if __name__ == '__main__':
    freeze_support()
    wrap_crawl(args.url, args.threads, args.agent, args.proxy, args.timeout, args.robots, args.max_urls, args.data_format)