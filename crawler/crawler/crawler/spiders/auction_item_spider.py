import json
import scrapy


class AuctionItemSpider(scrapy.Spider):
    name = "auction_item"

    def start_requests(self):
        with open('auction_list_real.json') as json_file:
            item_db = json.load(json_file)
            for item_dict in item_db:
                for item in item_dict['items']:
                    yield self.request(item)

    def parse(self, response):
        with open('items/' + response.request.item_id + '.html', 'wb') as fp:
            fp.write(response.body)

    def request(self, item):
        url = f'http://www.auctioning.co.kr/auction/detail_view_h.php?idx={item}'
        req = scrapy.Request(url, self.parse)
        req.item_id = item
        return req
