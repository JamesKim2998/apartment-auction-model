import os
import json
import scrapy


class AuctionItemSpider(scrapy.Spider):
    name = "auction_item"

    def start_requests(self):
        with open('auction_list_real.json') as json_file:
            item_db = json.load(json_file)

        for item_dict in item_db:
            for item in item_dict['items']:
                if not os.path.exists(AuctionItemSpider.get_save_path(item)):
                    yield self.request(item)

    @classmethod
    def get_save_path(cls, item_id):
        return 'items/' + item_id + '.html'

    def parse(self, response, item_id):
        with open(AuctionItemSpider.get_save_path(item_id), 'wb') as fp:
            fp.write(response.body)

    def request(self, item_id):
        url = f'http://www.auctioning.co.kr/auction/detail_view_h.php?idx={item_id}'
        return scrapy.Request(url, lambda response: self.parse(response, item_id))
