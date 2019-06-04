import os
import json
import scrapy


class UbatItemSpider(scrapy.Spider):
    name = "ubat_item"

    def start_requests(self):
        with open('ubat_list_2016_2019.json') as json_file:
            item_db = json.load(json_file)

        for item in item_db:
            if item['event_no1'] == '2015' or item['event_no1'] == '2016':
                continue
            if not os.path.exists(UbatItemSpider.get_save_path(item)):
                yield self.request(item)

    @classmethod
    def get_save_path(cls, item):
        return f'{item["event_no1"]}/{item["courtnum"]}_{item["event_no1"]}_{item["event_no2"]}_{item["obj_id"]}.html'

    def parse(self, response, item):
        with open(UbatItemSpider.get_save_path(item), 'wb') as fp:
            fp.write(response.body)

    def request(self, item):
        url = f'http://www.ubat.co.kr/auctionInfo/view_print.php?courtNo={item["courtnum"]}&courtNo2=&eventNo1={item["event_no1"]}&eventNo2={item["event_no2"]}&objNo={item["obj_id"]}'
        return scrapy.Request(url, lambda response: self.parse(response, item))
