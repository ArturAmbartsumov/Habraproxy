# coding=utf-8
import BaseHTTPServer
import argparse
import sys
from urlparse import urljoin
import requests
from bs4 import BeautifulSoup, element
import re
from urlparse import urlsplit, urlunsplit


PROXY_HOST = ''
DOMAIN = ''


def clean_domain(domain):
    domain = domain.replace('https://', '')
    domain = domain.replace('http://', '')
    return domain


def get_page(url):
    r = requests.get(urljoin(PROXY_HOST, url))
    return r


def process_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    excluded_tags = ['style', 'script']

    proxy_host = clean_domain(PROXY_HOST)
    for tag in soup.find_all(name='a', ):
        url = urlsplit(tag.get('href', ''))
        if url.netloc.startswith(proxy_host) or url.netloc.startswith('www.' + proxy_host):
            url = url._replace(scheme='http')
            url = url._replace(netloc=DOMAIN)
            tag['href'] = urlunsplit(url)

    for t in soup.find_all(text=True):
        if t.parent.name not in excluded_tags and t.__class__ == element.NavigableString:
            text = unicode(t)
            word_list = list(set(re.findall(r'\b[\w]{6}\b', text, re.U)))
            for word in word_list:
                text = text.replace(word, word + u"\u2122")
            t.replaceWith(text)
    return str(soup)


class ProxyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    # Handler for the GET requests
    def do_GET(self):
        r = get_page(self.path)


        content_type = r.headers.get('Content-Type')
        if content_type and content_type.find('html') != -1:
            self.send_response(r.status_code)
            self.send_header('Content-Type', 'text/html')

            self.end_headers()

            text = process_html(r.text.encode(r.encoding))
            self.wfile.write(text)
        else:
            self.send_response(301)
            self.send_header('Location', urljoin(PROXY_HOST, self.path))
            self.end_headers()
            self.wfile.write('')


def main(*args, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default=8080)
    parser.add_argument('-n', '--host', default='127.0.0.1')
    parser.add_argument('-d', '--domain', default=None)
    parser.add_argument('-s', '--site', default='https://habrahabr.ru')
    namespace = parser.parse_args(sys.argv[1:])

    try:
        port = int(namespace.port)
    except ValueError:
        port = 8080
    host = namespace.host
    global PROXY_HOST
    PROXY_HOST = namespace.site
    global DOMAIN
    DOMAIN = namespace.domain if namespace.domain else '{0}:{1}'.format(host, port)

    server = BaseHTTPServer.HTTPServer((host, port), ProxyHandler)
    print 'Started httpserver on {0}:{1}'.format(host, port)
    print 'Site {0}'.format(PROXY_HOST)

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print 'shutting down the web server'
        server.socket.close()


if __name__ == '__main__':
    main()
