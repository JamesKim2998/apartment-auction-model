import scrapy


class UbatListSpider(scrapy.Spider):
    name = "ubat_list"

    def start_requests(self):
        # for year in range(2007, 2020):
        for year in range(2010, 2016):
            for month in range(1, 13):
                for day in range(1, 32):
                    yield self.request(year, month, day)

    def parse(self, response):
        xpath = '//tr[@style="cursor:hand"]'
        selectors = response.xpath(xpath)
        item_list = list(map(lambda x: x.root, selectors))
        for item in item_list:
            courtnum, event_no1, event_no2, other = item.attrib['onclick'].split('?')[1].split('&')[:4]
            courtnum = courtnum.split('=')[1]
            event_no1 = event_no1.split('=')[1]
            event_no2 = event_no2.split('=')[1]
            obj_id = other.split('\'')[0].split('=')[1]
            yield {'courtnum': courtnum, 'event_no1': event_no1, 'event_no2': event_no2, 'obj_id': obj_id}

    def request(self, year, month, day):
        url = 'http://www.ubat.co.kr/v1/info.htm?'
        query_str = f'sell_yyyy_s={year}&sell_mm_s={month:02d}&sell_dd_s={day:02d}' \
            f'&sell_yyyy_e={year}&sell_mm_e={month:02d}&sell_dd_e={day:02d}' \
            f'&use1=01%2C&list_view_cnt=1000'
        return scrapy.Request(url + query_str, self.parse)
