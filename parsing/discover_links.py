from lxml import html as lh
from urllib.parse import urljoin, urlparse, urldefrag


def discover_internal_links(base_url, user_agent, response_object, robots_rules):
    links = []
    try:
        dom = lh.fromstring(response_object.text)
        for href in dom.xpath('//a/@href'):
            url = urldefrag(urljoin(base_url, href))[0]
            if urlparse(url).netloc == urlparse(base_url).netloc:
                if robots_rules and robots_rules.is_allowed(user_agent, url):
                    links.append(url)
                elif not robots_rules:
                    links.append(url)
        return links
    except Exception as e:
        print(e)
        return links