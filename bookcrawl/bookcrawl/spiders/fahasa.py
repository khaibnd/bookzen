# -*- coding: utf-8 -*-
import datetime
import socket
from urllib import urlencode
import re

import scrapy
from scrapy.http import Request
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst, Join
from scrapy.linkextractors import LinkExtractor
from scrapy_splash import SplashRequest

from unidecode import unidecode
from bookcrawl.items import BooksItem

script = """
function main(splash)
    splash:init_cookies(splash.args.cookies)
    local url = splash.args.url
    assert(splash:go(url))
    assert(splash:wait(5))

    return {
        cookies = splash:get_cookies(),
        html = splash:html()
    }
end
"""

script2 = """
function main(splash)
    splash:init_cookies(splash.args.cookies)
    local url = splash.args.url
    assert(splash:go(url))
    assert(splash:wait(0.5))

    return {
        cookies = splash:get_cookies(),
        html = splash:html()
    }
end
"""


class FahasaSpider(scrapy.Spider):
    name = 'fahasa'
    allowed_domains = ['fahasa.com']
    start_urls = [
            "https://www.fahasa.com/sach-trong-nuoc/van-hoc-trong-nuoc.html",
            "https://www.fahasa.com/sach-trong-nuoc/van-hoc-dich.html",
            # "https://www.fahasa.com/sach-trong-nuoc/kinh-te-chinh-tri-phap-ly.html",
            # "https://www.fahasa.com/sach-trong-nuoc/tam-ly-ky-nang-song.html",
            # "https://www.fahasa.com/sach-trong-nuoc/kien-thuc-tong-hop.html",
            # "https://www.fahasa.com/sach-trong-nuoc/khoa-hoc-ky-thuat.html",
            # "https://www.fahasa.com/sach-trong-nuoc/tu-dien.html",
            # "https://www.fahasa.com/sach-trong-nuoc/sach-hoc-ngoai-ngu.html",
            # "https://www.fahasa.com/foreigncategory.html",
            ]

    # rules = (
    #     Rule(LinkExtractor(
    #         restrict_xpaths='//*[@title="Next"]'),
    #         process_links='process_links'),
    #     Rule(LinkExtractor(
    #         restrict_xpaths='//*[@class="product-name p-name-list"]/a'),
    #         process_links='process_links',
    #         callback='parse_item'),
    # )

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, endpoint='execute',
                                args={'lua_source': script})

    def parse(self, response):
        # Get the next page and yield Request
        next_selector = response.xpath('//*[@title="Next"]/@href')
        for url in next_selector.extract():
            yield SplashRequest(url, endpoint='execute',
                                args={'lua_source': script2})

        # Get URL in page and yield Request
        url_selector = response.xpath(
            '//*[@class="product-name p-name-list"]/a/@href')
        for url in url_selector.extract():
            yield SplashRequest(url, callback=self.parse_item,
                                endpoint='execute',
                                args={'lua_source': script2})

    def parse_item(self, response):
        """
        @url http://www.fahasa.com/luat-im-lang-mario-puzo.html
        @returns items 1
        @scrapes name name_unidecode price description
        @scrapes url project spider server date
        """
        l = ItemLoader(item=BooksItem(), response=response)

        l.add_value('name', l.get_xpath(
                                '//*[@class="product-name"]/h1/text()')[-1])
        l.add_value('name_unidecode', unidecode(l.get_xpath(
                                '//*[@class="product-name"]/h1/text()')[-1]))
        l.add_xpath('price', '//*[@class="price-box"]/p[1]/span[2]/text()',
                    TakeFirst(), re=r'\d+\.\d+')
        l.add_value('description',
                    filter(None,
                           [re.sub('<[^<]+?>', '', i) for i in l.get_xpath('//*[@class="std"]')]),
                    Join('\n'))
        l.add_xpath('image_uri', '//*[@id="image"]/@src')

        # Information fields
        l.add_value('url', response.url)
        l.add_value('project', self.settings.get('BOT_NAME'))
        l.add_value('spider', self.name)
        l.add_value('server', socket.gethostname())
        l.add_value('date', datetime.datetime.now())

        return l.load_item()
