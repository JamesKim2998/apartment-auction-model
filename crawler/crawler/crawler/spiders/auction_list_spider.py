import scrapy


class AuctionListSpider(scrapy.Spider):
    name = "auction_list"

    def start_requests(self):
        for year in range(2007, 2020):
            for month in range(1, 13):
                yield self.request(year, month, 1)

    def parse(self, response):
        xpath = '//input/@value'
        selectors = response.xpath(xpath)
        item_list = list(map(lambda x: x.root, selectors))[:-1]

        year, month, day = response.request.date
        date_str = f'{year}-{month:02d}-{day:02d}'
        yield {'date': date_str, 'items': item_list}

        if day != 31:
            new_day = day + 1
            yield self.request(year, month, new_day)

    def request(self, year, month, day):
        url = 'http://www.auctioning.co.kr/auction/list_print.php?'
        date_str = f'{year}-{month:02d}-{day:02d}'
        query_str = f'ipdate1={date_str}&ipdate2={date_str}&search_usage2=101'

        req = scrapy.Request(url + query_str, self.parse)
        req.date = [year, month, day]
        return req
