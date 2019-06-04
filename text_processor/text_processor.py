import os
import codecs
import re
import jsonpickle
from lxml import etree

parser = etree.HTMLParser()


class NotCompletedItemException(Exception):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ItemInfo(object):
    __slots__ = [
        '매각기일',
        '소재지1', '소재지2', '소재지3', '층',
        '건수', '최저가', '전용면적', '매각대상', '청구금액', '사건접수',
        '유찰회수', '낙찰가',
        '감정평가_토지', '감정평가_건물',
        '임차인_보증금', '임차인_월세',
        '환경_토지경사', '환경_토지평탄', '환경_토지정방형', '환경_토지부정형',
        '환경_한강', '환경_용이', '환경_혼재', '환경_대중교통',
        '환경_단지', '환경_상가', '환경_학교', '환경_공원', '환경_공공시설', '환경_병원', '환경_종교',
        '환경_농경지', '환경_승강기', '환경_경보기',
        '지역분석',
    ]

    def to_tsv(self):
        attrs = [
            self.매각기일,
            self.소재지1, self.소재지2, self.소재지3, self.층,
            self.건수, self.최저가, self.전용면적, self.매각대상, self.청구금액, self.사건접수,
            self.유찰회수, self.낙찰가,
            self.감정평가_토지, self.감정평가_건물,
            self.임차인_보증금, self.임차인_월세,
            self.환경_토지경사, self.환경_토지평탄, self.환경_토지정방형, self.환경_토지부정형,
            self.환경_한강, self.환경_용이, self.환경_혼재, self.환경_대중교통,
            self.환경_단지, self.환경_상가, self.환경_학교, self.환경_공원, self.환경_공공시설, self.환경_병원, self.환경_종교,
            self.환경_농경지, self.환경_승강기, self.환경_경보기,
            self.지역분석, ]
        attrs = list(map(lambda x: str(x), attrs))
        return '\t'.join(attrs)


토지경사_label = ['완만', '완경사']
토지평탄_label = ['평탄']
토지정방형_label = ['정방형', '장방형']
토지부정형_label = ['부정형', '자루형']
한강_label = ['한강']
용이_label = ['용이']
혼재_label = ['혼재']
대중교통_label = ['승강장', '정류장', '지하철', '전철', '역']
단지_label = ['대규모', '단지', '근린']
상가_label = ['근린', '상가', '점포']
학교_label = ['학교', '고교', '교육']
공원_label = ['녹지', '공원']
공공시설_label = ['관청', '법원', '검찰청', '문화', '주민', '센터', '청사']
병원_label = ['병원']
종교_label = ['성당', '교회']
농경지_label = ['농경', '임야']
승강기_label = ['승강기']
경보기_label = ['경보기']


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
    address_tokens = cols[1].xpath('table/tr/td/b/font')[0].text.split('\r\n')[0].split()
    result.소재지1 = address_tokens[0]
    result.소재지2 = address_tokens[1]
    result.소재지3 = address_tokens[2]
    result.층 = None
    for address_token in address_tokens[3:]:
        if '조표' in address_token:
            continue
        if address_token == '제지층':
            result.층 = 0
            break
        if address_token.endswith('층'):
            if address_token.startswith('제') and not address_token[1].isdigit():
                continue
            if ',' in address_token:
                address_token = address_token.split(',')[1]
            if '지하' in address_token:
                result.층 = 0
            elif address_token.startswith('제'):
                result.층 = int(address_token[1:-1])
            else:
                result.층 = int(address_token[:-1])
            break
        elif '층' in address_token:
            maybe_층 = address_token.split('층')[0]
            if maybe_층.isdigit():
                result.층 = int(maybe_층)
                break
        elif address_token.endswith('호'):
            maybe_호 = address_token.replace('제', '').replace('호', '')
            if maybe_호.isdigit():
                result.층 = int(maybe_호) // 100
                break

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
    최저가_text = cols[5].find('font').text
    result.최저가 = int(최저가_text.split(' ')[1][:-1].replace(',', ''))
    cols = rows[3].findall('td')
    전용면적_text = cols[1].text
    if not 전용면적_text or 전용면적_text == '  ':
        raise NotCompletedItemException()
    result.전용면적 = float(전용면적_text.split('㎡')[0])
    # 보증금 = cols[5].find('font').text  # 보증금은 최저가의 10%임
    cols = rows[4].findall('td')
    매각대상_text = cols[3].text
    if 매각대상_text == None:
        매각대상_text = cols[3].xpath('font/text()')[0]
    if 매각대상_text == '토지/건물일괄매각':
        result.매각대상 = 1
    elif 매각대상_text == '토지/건물지분매각':
        result.매각대상 = 2
    elif 매각대상_text == '토지매각':
        result.매각대상 = 3
    elif 매각대상_text == '건물만매각':
        result.매각대상 = 4
    elif 매각대상_text == '건물지분매각':
        result.매각대상 = 5
    elif 매각대상_text == '전세권매각':
        result.매각대상 = 6
    else:
        raise Exception('Undefined 매각대상: ' + str(매각대상_text))
    result.청구금액 = int(cols[5].text[:-1].replace(',', ''))
    cols = rows[5].findall('td')
    result.사건접수 = cols[1].text
    # result.배당종기일 = cols[3].text
    # 개시결정 = cols[5].text  # 개시결정은 사건접수 다음날임.

    # tables[2]: 기일현황
    result.유찰회수 = 0
    result.낙찰가 = None
    rows = tables[2].xpath('//table[@class="LineTable"]/tr')
    i = 1
    while i < len(rows):
        cols = rows[i].findall('td')

        if cols[0].text is None:
            i += 1
            continue

        if len(cols) == 3 and cols[2].xpath('font/font/text()')[0]:
            raise NotCompletedItemException()
        # 회차 = cols[0].text
        # 회차_최저매각금액 = cols[2].text.rstrip()
        회차_결과 = cols[3].text or cols[3].find('font').text
        # print(회차, 회차_매각기일, 회차_최저매각금액, 회차_결과)
        i += 1

        if i >= len(rows):
            break

        if 회차_결과 == '유찰':
            result.유찰회수 += 1
        elif 회차_결과 == '매각':
            row = rows[i]
            maybe_낙찰가 = row.xpath('td/font/font/font[2]')
            if len(maybe_낙찰가) == 0:
                maybe_낙찰가 = row.xpath('td/font/font/font')
            if len(maybe_낙찰가) > 0:
                낙찰가_text = maybe_낙찰가[0].text
                result.낙찰가 = int(낙찰가_text[2:].split('원')[0].replace(',', ''))
            elif '취하' in row.xpath('td/font/font/text()')[0]:
                raise NotCompletedItemException()
            else:
                # 최저가에 매각되었음을 의미
                result.낙찰가 = result.최저가
            i += 1

        회차_매각기일 = cols[1].text
        if 회차_매각기일 == result.매각기일:
            break
    if 회차_결과 == '취하' or 회차_결과 == '변경':
        raise NotCompletedItemException()

    # tables[2]: 감정평가
    cols = tables[2].findall('tr')[2].findall('td')
    감정평가_토지_text = cols[0].text
    if 감정평가_토지_text != 'x':
        result.감정평가_토지 = int(감정평가_토지_text[:-1].replace(',', ''))
    else:
        result.감정평가_토지 = 0
    감정평가_건물_text = cols[1].text
    if 감정평가_건물_text != 'x':
        result.감정평가_건물 = int(감정평가_건물_text[:-1].replace(',', ''))
    else:
        result.감정평가_건물 = 0
    # 감정평가_제시외건물_포함 = cols[2].text  # 아파트의 경우, 보통 없다.
    # 감정평가_제시외건물_제외 = cols[3].text  # 아파트의 경우, 보통 없다.
    # 기타_가계기구 = cols[4].text  # 아파트의 경우, 보통 없다.
    # 합계 = cols[5].text
    # print(result.감정평가_토지, result.감정평가_건물)

    # tables[3]: 지역분석
    tokens = tables[3].xpath('tr[1]/td[2]//text()')
    result.지역분석 = ' '.join(tokens)

    def check_label(text, label):
        return any(map(lambda x: x in text, label)) and 1 or 0

    result.환경_토지경사 = check_label(result.지역분석, 토지경사_label)
    result.환경_토지평탄 = check_label(result.지역분석, 토지평탄_label)
    result.환경_토지정방형 = check_label(result.지역분석, 토지정방형_label)
    result.환경_토지부정형 = check_label(result.지역분석, 토지부정형_label)
    result.환경_한강 = check_label(result.지역분석, 한강_label)
    result.환경_용이 = check_label(result.지역분석, 용이_label)
    result.환경_혼재 = check_label(result.지역분석, 혼재_label)
    result.환경_대중교통 = check_label(result.지역분석, 대중교통_label)
    result.환경_단지 = check_label(result.지역분석, 단지_label)
    result.환경_상가 = check_label(result.지역분석, 상가_label)
    result.환경_학교 = check_label(result.지역분석, 학교_label)
    result.환경_공원 = check_label(result.지역분석, 공원_label)
    result.환경_공공시설 = check_label(result.지역분석, 공공시설_label)
    result.환경_병원 = check_label(result.지역분석, 병원_label)
    result.환경_종교 = check_label(result.지역분석, 종교_label)
    result.환경_농경지 = check_label(result.지역분석, 농경지_label)
    result.환경_승강기 = check_label(result.지역분석, 승강기_label)
    result.환경_경보기 = check_label(result.지역분석, 경보기_label)

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
    file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2019/E01_2019_97_1.html'
    file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2019/L01_2019_61008_1.html'
    file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2017/I03_2017_6619_1.html'
    file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2017/B03_2017_2671_1.html'
    file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2014/A01_2014_18859_1.html'
    file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2014/L01_2014_1223_1.html'
    file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2015/G01_2015_6459_1.html'
    file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2015/N01_2015_10839_1.html'
    file_path = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_2012/A01_2012_29855_1.html'
    file_path = None

    if file_path:
        print(file_path)
        result = parse_file(file_path)
        print(jsonpickle.encode(result, unpicklable=False))
        exit(0)

    for year in range(2012, 2020):
        year_str = str(year)
        output = codecs.open(year_str + '.tsv', encoding='utf-8', mode='w')
        output.write('파일이름\t' + '\t'.join(ItemInfo().__slots__) + '\n')

        root_dir = '/Users/jameskim/Develop/Personal/apartment-auction-model/dataset/ubat_' + year_str
        for _, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename == '.DS_Store':
                    continue
                file_path = os.path.join(root_dir, filename)
                # print(file_path)
                try:
                    result = parse_file(file_path)
                    output.write(filename + '\t' + result.to_tsv() + '\n')
                    # print(jsonpickle.encode(result, unpicklable=False))
                except NotCompletedItemException as e:
                    pass
                except Exception as e:
                    print('Parsing failed\n' + file_path)
                    print(e)

        output.close()
