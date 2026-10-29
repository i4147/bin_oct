#!/data/data/com.termux/files/usr/bin/env python
from __future__ import annotations

import curses
import logging
import logging.config
import logging.handlers
import os
import re
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from sqlalchemy import Boolean, Column, Integer, MetaData, Table, Unicode, create_engine, select

DEBUG = True
USE_COLORS = True
DATABASE_NAME = "data/crawler.sqlite"
HTML_DIR = "data/html/"
EMAILS_FILENAME = "data/emails.csv"
DOMAINS_FILENAME = "data/domains.csv"
MAX_SEARCH_RESULTS = 150
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "[%(asctime)s] %(levelname)s::%(module)s - %(message)s",
        },
        "file": {
            "format": "[%(asctime)s] %(levelname)s::(P:%(process)d T:%(thread)d)::%(module)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "()": "ColorStreamHandler",
            "formatter": "console",
            "level": "DEBUG",
            "use_colors": USE_COLORS,
        },
        "file": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "formatter": "file",
            "level": "INFO",
            "when": "midnight",
            "filename": "logs/pycrawler.log",
            "interval": 1,
            "backupCount": 0,
            "encoding": None,
            "delay": False,
            "utc": False,
        },
    },
    "loggers": {
        "crawler_logger": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
    },
}


class ColorStreamHandler(logging.Handler):
    def __init__(self, use_colors=True):
        logging.Handler.__init__(self)
        self.use_colors = use_colors
        try:
            curses.setupterm()
            self.fcap = curses.tigetstr("setaf")
            self.COLOR_NORMAL = curses.tigetstr("sgr0")
            self.COLOR_INFO = curses.tparm(self.fcap, curses.COLOR_GREEN)
            self.COLOR_ERROR = curses.tparm(self.fcap, curses.COLOR_RED)
            self.COLOR_WARNING = curses.tparm(self.fcap, curses.COLOR_YELLOW)
            self.COLOR_DEBUG = curses.tparm(self.fcap, curses.COLOR_BLUE)
        except Exception:
            self.use_colors = False
            self.COLOR_NORMAL = self.COLOR_INFO = self.COLOR_ERROR = b""
            self.COLOR_WARNING = self.COLOR_DEBUG = b""

    def color(self, msg, level):
        if level == "INFO":
            return "%s%s%s" % (self.COLOR_INFO, msg, self.COLOR_NORMAL)
        elif level == "WARNING":
            return "%s%s%s" % (self.COLOR_WARNING, msg, self.COLOR_NORMAL)
        elif level == "ERROR":
            return "%s%s%s" % (self.COLOR_ERROR, msg, self.COLOR_NORMAL)
        elif level == "DEBUG":
            return "%s%s%s" % (self.COLOR_DEBUG, msg, self.COLOR_NORMAL)
        return msg

    def emit(self, record):
        try:
            if isinstance(record.msg, str):
                record.msg = record.msg.encode("utf-8", "ignore").decode("utf-8", "ignore")
            msg = self.format(record)
            temp = msg.split("]")
            if len(temp) > 1:
                msg = "[" + temp[0].split(" ")[1].split(",")[0] + "]" + temp[1]
            if self.use_colors:
                msg = self.color(msg, record.levelname)
            print(msg)
        except Exception:
            self.handleError(record)


import sys as _sys

_sys.modules[__name__].ColorStreamHandler = ColorStreamHandler
logging.config.dictConfig(LOGGING)
logger = logging.getLogger("crawler_logger")


class CrawlerDb:
    def __init__(self):
        self.connected = False

    def connect(self):
        Path(DATABASE_NAME).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine("sqlite:///" + DATABASE_NAME)
        self.connection = self.engine.connect()
        self.connected = True if self.connection else False
        self.metadata = MetaData()
        self.website_table = Table(
            "website",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("url", Unicode, nullable=False),
            Column("has_crawled", Boolean, default=False),
            Column("emails", Unicode, nullable=True),
        )
        self.metadata.create_all(self.engine)

    def enqueue(self, url, emails=None):
        if not self.connected:
            return False
        s = select([self.website_table]).where(self.website_table.c.url == url)
        res = self.connection.execute(s)
        result = res.fetchall()
        res.close()
        if len(result) > 0:
            return False
        args = [{"url": str(url)}]
        if emails is not None:
            args = [{"url": str(url), "has_crawled": True, "emails": str(",".join(emails))}]
        result = self.connection.execute(self.website_table.insert(), args)
        self.connection.commit()
        return bool(result)

    def dequeue(self):
        if not self.connected:
            return False
        s = select([self.website_table]).limit(1).where(self.website_table.c.has_crawled == False)
        res = self.connection.execute(s)
        result = res.fetchall()
        res.close()
        if len(result) > 0:
            return result[0]
        return False

    def crawled(self, website, new_emails=None):
        if not self.connected:
            return False
        stmt = (
            self.website_table
            .update()
            .where(self.website_table.c.id == website.id)
            .values(has_crawled=True, emails=new_emails)
        )
        self.connection.execute(stmt)
        self.connection.commit()
        return None

    def get_all_emails(self):
        if not self.connected:
            return None
        s = select([self.website_table])
        res = self.connection.execute(s)
        results = res.fetchall()
        res.close()
        email_set = set()
        for result in results:
            if result.emails is None:
                continue
            for email in result.emails.split(","):
                email_set.add(email)
        return email_set

    def get_all_domains(self):
        if not self.connected:
            return None
        s = select([self.website_table])
        res = self.connection.execute(s)
        results = res.fetchall()
        res.close()
        domain_set = set()
        for result in results:
            if result.url is None:
                continue
            url = urllib.parse.urlparse(result.url)
            hostname = url.hostname.split(".")
            hostname = ".".join((len(hostname[-2]) < 4 and hostname[-3:]) or hostname[-2:])
            domain_set.add(hostname)
        return domain_set

    def close(self):
        self.connection.close()

    def save_html(self, filename, html):
        Path(HTML_DIR).mkdir(parents=True, exist_ok=True)
        path = os.path.join(HTML_DIR, filename)
        with open(path, "w+", encoding="utf-8", errors="replace") as f:
            f.writelines(html)


google_adurl_regex = re.compile('adurl=(.*?)"')
google_url_regex = re.compile("url\\?q=(.*?)&amp;sa=")
email_regex = re.compile("([A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,4})", re.IGNORECASE)
url_regex = re.compile("<a\\s.*?href=['\"](.*?)['\"].*?>")
db = CrawlerDb()
db.connect()


def retrieve_html(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Just-Crawling 0.1")
    request = None
    status = 0
    try:
        logger.info("Crawling %s" % url)
        request = urllib.request.urlopen(req)
    except urllib.error.URLError as e:
        logger.error("Exception at url: %s\n%s" % (url, e))
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        return None
    if status == 0:
        status = 200
    try:
        data = request.read()
    except Exception as e:
        return None
    return str(data)


def find_emails_in_html(html):
    if html is None:
        return set()
    email_set = set()
    for email in email_regex.findall(html):
        email_set.add(email)
    return email_set


def find_links_in_html_with_same_hostname(url, html):
    if html is None:
        return set()
    url = urllib.parse.urlparse(url)
    links = url_regex.findall(html)
    link_set = set()
    for link in links:
        if link is None:
            continue
        try:
            link = str(link)
            if link.startswith("/"):
                link_set.add("http://" + url.netloc + link)
            elif link.startswith(("http", "https")):
                if link.find(url.netloc):
                    link_set.add(link)
            elif link.startswith("#"):
                continue
            else:
                link_set.add(urllib.parse.urljoin(url.geturl(), link))
        except Exception as e:
            pass
    return link_set


def find_emails_2_level_deep(url):
    html = retrieve_html(url)
    email_set = find_emails_in_html(html)
    if len(email_set) > 0:
        return email_set
    else:
        logger.info("No email at level 1.. proceeding to crawl level 2")
        link_set = find_links_in_html_with_same_hostname(url, html)
        for link in link_set:
            html = retrieve_html(link)
            if html is None:
                continue
            email_set = find_emails_in_html(html)
            db.enqueue(link, list(email_set))
        return set()


def crawl(keywords):
    logger.info("-" * 40)
    logger.info("Keywords to Google for: %s" % keywords)
    logger.info("-" * 40)
    for page_index in range(0, MAX_SEARCH_RESULTS, 10):
        query = {"q": keywords}
        url = "http://www.google.com/search?" + urllib.parse.urlencode(query) + "&start=" + str(page_index)
        data = retrieve_html(url)
        for u in google_url_regex.findall(data or ""):
            db.enqueue(str(u))
        for u in google_adurl_regex.findall(data or ""):
            db.enqueue(str(u))
    while True:
        uncrawled = db.dequeue()
        if uncrawled is False:
            break
        email_set = find_emails_2_level_deep(uncrawled.url)
        if len(email_set) > 0:
            db.crawled(uncrawled, ",".join(list(email_set)))
        else:
            db.crawled(uncrawled, None)


if __name__ == "__main__":
    try:
        arg = sys.argv[1].lower()
        if arg in {"--emails", "-e"}:
            logger.info("=" * 40)
            logger.info("Processing...")
            emails = db.get_all_emails()
            logger.info("There are %d emails" % len(emails))
            Path(EMAILS_FILENAME).parent.mkdir(parents=True, exist_ok=True)
            with open(EMAILS_FILENAME, "w+") as file:
                file.writelines("\n".join(emails))
            logger.info("All emails saved to ./data/emails.csv")
            logger.info("=" * 40)
        elif arg in {"--domains", "-d"}:
            logger.info("=" * 40)
            logger.info("Processing...")
            domains = db.get_all_domains()
            logger.info("There are %d domains" % len(domains))
            Path(DOMAINS_FILENAME).parent.mkdir(parents=True, exist_ok=True)
            with open(DOMAINS_FILENAME, "w+") as file:
                file.writelines("\n".join(domains))
            logger.info("All domains saved to ./data/domains.csv")
            logger.info("=" * 40)
        else:
            crawl(arg)
    except KeyboardInterrupt:
        logger.error("Stopping (KeyboardInterrupt)")
        sys.exit()
    except Exception as e:
        logger.error("EXCEPTION: %s " % e)
        traceback.print_exc()
