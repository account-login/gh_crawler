#!/usr/bin/env python3

import argparse
import os
import re
import logging
import html.parser
import requests


logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)5s %(asctime)s.%(msecs)03d [%(processName)s:%(process)d] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

L = logging.getLogger(__name__)


# https://github.com/torvalds/linux/tree/master/drivers/crypto/allwinner
def parse_url(url):
    org, repo, _, tree, path = re.match(
        r'^https://github.com/([^/]+)/([^/]+)/(tree|blob)/([^/]+)/(.+)$',
        url,
    ).groups()
    return org, repo, tree, path


def write_file(path, data):
    dirname = os.path.dirname(path)
    os.makedirs(dirname, exist_ok=True)
    with open(path, 'wb') as fp:
        fp.write(data)


def crawl_blob(session: requests.Session, url):
    L.info('starting blob: %s', url)
    org, repo, tree, path = parse_url(url)
    raw_url = f'https://raw.githubusercontent.com/{org}/{repo}/{tree}/{path}'
    data = session.get(raw_url).content
    write_file(path, data)
    L.info('finished blob: %s', url)


def crawl_tree(session: requests.Session, url):
    class Parser(html.parser.HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag != 'a':
                return
            href = dict(attrs).get('href', '')
            if href.startswith(tree_prefix):
                crawl_tree(session, f'https://github.com{href}')
            elif href.startswith(blob_prefix):
                crawl_blob(session, f'https://github.com{href}')

    L.info('starting tree: %s', url)
    org, repo, tree, path = parse_url(url)
    tree_prefix = f'/{org}/{repo}/tree/{tree}/{path}'
    blob_prefix = f'/{org}/{repo}/blob/{tree}/{path}'
    text = session.get(url).text
    parser = Parser()
    parser.feed(text)
    L.info('finished tree: %s', url)


# TODO: threading
# TODO: file permissions
# TODO: resolve tree name to hash
# TODO: control output directory
# TODO: use api: https://developer.github.com/v3/repos/contents/
#       https://api.github.com/repos/torvalds/linux/contents/drivers/crypto/allwinner?ref=master
# TODO: check sha1 before download
# TODO: support root directory
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('url')

    args = ap.parse_args()
    with requests.session() as session:
        crawl_tree(session, args.url)


if __name__ == '__main__':
    main()
