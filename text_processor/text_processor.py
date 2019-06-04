import os
import codecs
import re
import jsonpickle
from lxml import etree

parser = etree.HTMLParser()


class ItemInfo(object):
    __slots__ = [
        '매각기일', '소재지', '건수', '최저가', '전용면적', '매각대상', '청구금액', '사건접수', '배당종기일',
        '유찰회수', '낙찰가',
        '감정평가_토지', '감정평가_건물',
        '지역분석',
        '임차인_보증금', '임차인_월세',
    ]

    def to_tsv(self):
        attrs = [
            self.매각기일, self.소재지, self.건수, self.최저가, self.전용면적, self.청구금액, self.사건접수, self.배당종기일,
            self.유찰회수, self.낙찰가,
            self.감정평가_토지, self.감정평가_건물,
            self.지역분석,
            self.임차인_보증금, self.임차인_월세]
        attrs = list(map(lambda x: str(x), attrs))
        return '\t'.join(attrs)


def parse_file(file_path: str) -> ItemInfo:
    with codecs.open(file_path, encoding='cp949', mode='r') as fp:
        file_contents = fp.read()
    file_contents = re.sub(r'<td .*?>', '<td>', file_contents)

    tree = etree.fromstring(file_contents, parser)
    tables = tree.xpath('//table[@bgcolor="#C6C6C6"]')

    result = ItemInfo()

    # tables[0]
    table = tables[0]
    result.매각기일 = table.xpath('tr/td/table/strong/tr/td[2]/b')[0].text.strip()[:10]

    # tables[1]
    rows = tables[1].findall('tr')
    cols = rows[0].findall('td')
    result.소재지 = cols[1].xpath('table/tr/td/b/font')[0].text.split('\r\n')[0]
    건수_list = cols[1].xpath('table/tr/td/font[@style="font-size:11px; letter-spacing:-1px;"]')
    result.건수 = 1
    if len(건수_list) > 0:
        result.건수 = int(건수_list[0].text[1:-1])
    # cols = rows[1].findall('td')
    # result.감정가 = cols[5].text  # 아래에서 한번 더 나온다.
    cols = rows[2].findall('td')
    # result.대지권 = cols[1].text
    # TODO: 대지권 미등기인 경우가 있음
    # 대지권 = cols[1].xpath('font/text()')[0]
    result.최저가 = cols[5].find('font').text
    cols = rows[3].findall('td')
    result.전용면적 = cols[1].text
    # 보증금 = cols[5].find('font').text  # 보증금은 최저가의 10%임
    cols = rows[4].findall('td')
    result.매각대상 = cols[3].text
    result.청구금액 = cols[5].text
    cols = rows[5].findall('td')
    result.사건접수 = cols[1].text
    result.배당종기일 = cols[3].text
    # 개시결정 = cols[5].text  # 개시결정은 사건접수 다음날임.

    # tables[2]: 기일현황
    result.유찰회수 = 0
    result.낙찰가 = 0
    rows = tables[2].xpath('.//table[@class="LineTable"]/tr')
    i = 1
    while i < len(rows):
        cols = rows[i].findall('td')

        if cols[0].text is None:
            i += 1
            continue

        # 회차 = cols[0].text
        # 회차_최저매각금액 = cols[2].text.rstrip()
        회차_결과 = cols[3].text or cols[3].find('font').text
        # print(회차, 회차_매각기일, 회차_최저매각금액, 회차_결과)
        i += 1

        if 회차_결과 == '유찰':
            result.유찰회수 += 1
        elif 회차_결과 == '매각':
            row = rows[i]
            result.낙찰가 = row.xpath('td/font/font/font[2]')[0].text
            i += 1

        회차_매각기일 = cols[1].text
        if 회차_매각기일 == result.매각기일:
            break

    # tables[2]: 감정평가
    cols = tables[2].findall('tr')[2].findall('td')
    result.감정평가_토지 = cols[0].text
    result.감정평가_건물 = cols[1].text
    # 감정평가_제시외건물_포함 = cols[2].text  # 아파트의 경우, 보통 없다.
    # 감정평가_제시외건물_제외 = cols[3].text  # 아파트의 경우, 보통 없다.
    # 기타_가계기구 = cols[4].text  # 아파트의 경우, 보통 없다.
    # 합계 = cols[5].text
    # print(result.감정평가_토지, result.감정평가_건물)

    # tables[3]: 지역분석
    tokens = tables[3].xpath('tr[1]/td[2]//text()')
    result.지역분석 = ' '.join(tokens)

    # tables[5]: 임차인현황
    rows = tables[5].findall('tr')
    # 임차인_숫자 = 0
    result.임차인_보증금 = 0
    result.임차인_월세 = 0
    for i in range(1, len(rows)):
        row = rows[i]
        cols = row.findall('td')
        if len(cols) != 5:
            continue
        cell_texts = cols[3].xpath('text()')
        for cell_text in cell_texts:
            if '미상' in cell_text:
                continue
            elif '【보】' in cell_text:
                result.임차인_보증금 = int(cell_text.replace('【보】', '').replace(',', '')[:-1])
            elif '【월】' in cell_text:
                result.임차인_월세 = int(cell_text.replace('【월】', '').replace(',', '')[:-1])
        if result.임차인_보증금 != 0 or result.임차인_월세 != 0:
            break
    return result


if __name__ == '__main__':
    jsonpickle.set_encoder_options('json', ensure_ascii=False, indent=4)

    # file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2017/A01_2017_1470_1.html'
    # file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2015/A01_2015_2578_1.html'
    # file_path = 'file:///Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2017/A01_2017_8198_1.html'
    # file_path = 'file:///Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2012/G01_2012_22368_1.html'
    # file_path = 'file:///Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2016/B01_2016_7462_1.html'
    # file_path = 'file:///Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2016/B02_2016_6182_1.html'
    # file_path = 'file:///Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2016/C01_2016_5094_1.html'
    # file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2017/C01_2017_28964_1.html'
    # file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2017/B01_2017_105363_1.html'
    # file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2017/H04_2017_617_1.html'
    # result = parse_file(file_path)
    # print(jsonpickle.encode(result, unpicklable=False))
    # exit(0)

    for year in range(2019, 2020):
        year_str = str(year)
        output = codecs.open(year_str + '.tsv', encoding='utf-8', mode='w')

        root_dir = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_' + year_str
        for _, _, filenames in os.walk(root_dir):
            for filename in filenames:
                file_path = os.path.join(root_dir, filename)
                # print(file_path)
                try:
                    result = parse_file(file_path)
                    output.write(result.to_tsv() + '\n')
                    # print(jsonpickle.encode(result, unpicklable=False))
                except Exception as e:
                    print('Parsing failed: ' + file_path)
                    print(e)

        output.close()
