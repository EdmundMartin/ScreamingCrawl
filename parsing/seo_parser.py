from bs4 import BeautifulSoup
import re
from collections import OrderedDict


class SeoParser:

    def __init__(self, response_object):

        self.url = response_object.url
        self.history = response_object.history
        self.html = response_object.text
        self.status = response_object.status_code
        self.soup = BeautifulSoup(self.html, 'lxml')

    def __strip_and_replace(self, text):
        text = text.strip()
        text.replace('\n', ' ')
        return text

    def _title(self):
        title = self.soup.find('title')
        if title:
            return self.__strip_and_replace(title.get_text())
        return None

    def _h1_parse(self):
        h1_result = [None, None]
        all_h1s = self.soup.find_all('h1')
        if all_h1s:
            for index, h1 in enumerate(all_h1s[:2]):
                h1_text = self.__strip_and_replace(h1.get_text())
                h1_result[index] = h1_text
        return h1_result[0], h1_result[1]

    def _h2_parse(self):
        h2_result = self.soup.find('h2')
        if h2_result:
            return self.__strip_and_replace(h2_result.get_text())

    def _word_count(self):
        text = self.soup.get_text()
        text = re.findall(r'\w+', text)
        return len(text)

    def _meta_description(self):
        meta_desc = self.soup.find('meta', {'name': 'description'}, content=True)
        if meta_desc:
            return self.__strip_and_replace(meta_desc['content'])
        return None

    def result_dictionary(self):
        dictionary = OrderedDict()
        dictionary['url'] = self.url
        dictionary['title'] = self._title()
        dictionary['status_code'] = self.status
        dictionary['h1_1'], dictionary['h1_2'] = self._h1_parse()
        dictionary['meta_description'] = self._meta_description()
        dictionary['h2'] = self._h2_parse()
        dictionary['word_count'] = self._word_count()
        return dictionary


def parse_seo(response_object):
    seo = SeoParser(response_object)
    return seo.result_dictionary()