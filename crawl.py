import requests
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from urllib.parse import urlparse
import robotexclusionrulesparser
from parsing.discover_links import discover_internal_links
from parsing.seo_parser import parse_seo
from threading import BoundedSemaphore
from queue import Queue, Empty
from result_db import db, ResultDB
import time
import csv


class Crawl:

    def __init__(self, start_url, threads=20, user_agent='Google', proxy=None, timeout=30, obey_robots=True,
                 max_urls=None, data_format='csv'):
        self.urls_to_crawl = Queue()
        self.urls_to_crawl.put(start_url)
        self.url_in_queue = {}
        self.base_domain = self.__parse_start_url(start_url)
        self.crawled_urls = set([])
        self.background_process = ProcessPoolExecutor(max_workers=2)
        self.thread_pool = ThreadPoolExecutor(max_workers=threads)
        self.timeout = timeout
        self.user_agent = self.__select_user_agent(user_agent)
        self.proxy = {'http': proxy, 'https': proxy}
        self.robots_exclusion = self.__build_exclusion(obey_robots, timeout)
        self.url_count = 0
        self.max_urls = max_urls
        self.add_to_crawl_sempahore = BoundedSemaphore(1)
        self.add_to_datastore_sempahore = BoundedSemaphore(1)
        self.data_format = data_format
        if self.data_format == 'csv':
            self.csv_name = 'crawl-{}.csv'.format(time.time())

    def __build_exclusion(self, obey_robots, timeout):
        if obey_robots:
            rerp = robotexclusionrulesparser.RobotExclusionRulesParser()
            rerp.fetch('{}/robots.txt'.format(self.base_domain), timeout)
            return rerp
        else:
            return None

    def __parse_start_url(self, start_url):
        parsed_url = urlparse(start_url)
        return '{}://{}'.format(parsed_url.scheme, parsed_url.netloc)

    def __select_user_agent(self, user_agent):
        user_agents = {
            'Google': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Google-Mobile':'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        }
        return user_agents.get(user_agent, 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)')

    def update_crawl_queue(self, result):
        result = result.result()
        if result:
            for link in result:
                with self.add_to_crawl_sempahore:
                    if link not in self.crawled_urls and link not in self.url_in_queue:
                        self.urls_to_crawl.put(link)
                        self.url_in_queue['link'] = True

    def write_to_db(self, result):
        if result:
            with self.add_to_datastore_sempahore:
                try:
                    ResultDB.create(url=result.get('url'), title=result.get('title'),
                                    status_code=result.get('status_code'), h1_1=result.get('h1_1'),
                                    h1_2=result.get('h1_2'), h2=result.get('h2'),
                                    meta_description=result.get('meta_description'), word_count=result.get('word_count'))
                except Exception as e:
                    print(e)
                finally:
                    self.url_count += 1

    def write_to_csv(self, result):
        if result:
            with self.add_to_datastore_sempahore:
                with open(self.csv_name, 'a') as csv_output:
                    writer = csv.writer(csv_output)
                    writer.writerow([result.get('url'), result.get('title'), result.get('status_code'), result.get('h1_1'),
                                    result.get('h1_2'), result.get('h2'),
                                    result.get('meta_description'), result.get('word_count')])

    def write_to_data_store(self, result):
        result = result.result()
        if self.data_format == 'csv':
            self.write_to_csv(result)
        else:
            self.write_to_db(result)

    def handle_response_callback(self, result):
        result = result.result()
        if result:
            links_to_crawl = self.background_process.submit(discover_internal_links, self.base_domain, self.user_agent,
                                                            result, self.robots_exclusion)
            links_to_crawl.add_done_callback(self.update_crawl_queue)
            seo_results = self.background_process.submit(parse_seo, result)
            seo_results.add_done_callback(self.write_to_data_store)

    def make_request(self, url):
        try:
            print('CRAWLING: {}'.format(url))
            return requests.get(url, proxies=self.proxy, headers={'User-Agent': self.user_agent}, timeout=self.timeout)
        except requests.RequestException as e:
            print(e)
            return
        except ConnectionError:
            return

    def run_crawler(self):
        while True:
            try:
                url = self.urls_to_crawl.get(timeout=self.timeout)
                if self.max_urls:
                    if self.url_count > self.max_urls:
                        break
                if url not in self.crawled_urls:
                    self.crawled_urls.add(url)
                    task = self.thread_pool.submit(self.make_request, url)
                    task.add_done_callback(self.handle_response_callback)
            except Empty:
                break
            except Exception as e:
                continue


if __name__ == '__main__':
    db.create_tables([ResultDB])
    c = Crawl('http://edmundmartin.com')
    c.run_crawler()
