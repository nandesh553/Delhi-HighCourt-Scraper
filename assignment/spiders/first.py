import scrapy
from scrapy_splash import SplashRequest
from scrapy.spiders import BaseSpider
import json
import re
import datetime
import requests
import traceback
from lxml import html

class MySpider(BaseSpider):
    name="test"

    custom_settings = {
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 5
    }

    def start_requests(self):

        for i in range(0,1):
            url = 'http://delhihighcourt.nic.in/dhc_case_status_list_new.asp'

            yield scrapy.Request(url, callback=self.get_page, meta={'splash':{'args':{'wait':'5'},'endpoint':'render.html'}})

    def get_page(self,response):

        domain = 'http://delhihighcourt.nic.in/'

        archive_link = response.xpath('//div[contains(@class,"page-navigation")]/a/@href').extract()[-1]
        last_page = archive_link.split('&')
        for i in last_page:
            if 'SRecNo=' in i:
                total_page = i.replace('SRecNo=','')
        
        total_page = 1600

        page_count = 0
        count = 0
        while count != total_page:
            url = 'http://delhihighcourt.nic.in/dhc_case_status_list_new.asp?ayear=&pyear=&SNo=&SRecNo='+ str(count) +'&dno=&dyear=&ctype=&cno=&cyear=&party=&adv='
            
            count += 8
            page_count += 1
            yield scrapy.Request(url, callback=self.parse_page, meta={'page_count': page_count,
                                'total_page': total_page,
                                'splash': {'args': {'wait': '5'},'endpoint': 'render.html'}})

    def parse_page(self,response):
        total_page = response.meta['total_page']
        page_count = response.meta['page_count']
        url = response.url

        print('\n')
        print('{} out of {} done'.format(page_count,total_page))
        print('-----URL :',url)

        res = response.xpath('//ul[contains(@class,"clearfix grid")]/li').extract()

        for temp in res:
            try:
                tree = html.fromstring(temp)
                res1 = tree.xpath('//span/text()')[1]+tree.xpath('//span/text()')[2]
                res2 = tree.xpath('//span/text()')[7]
                res3 = tree.xpath('//span/text()')[6] #respondent
                res4 = tree.xpath('//span/text()')[8]
                res5 = tree.xpath('//span/text()')[5] #petitioner

                try:
                    next_date = ''
                    last_date = ''
                    disposed_date = ''
                    status = ''

                    res6 = tree.xpath('//span/text()')[9]

                    temp2 = re.sub(r"\s+", " ", res6).strip()
                    
                    if((temp2.find("Next")) != -1):
                        next_date = temp2.split(':')[1].strip()
                    elif((temp2.find("DISPOSED")) != -1):
                        disposed_date = temp2.split()[-1].strip()
                    elif((temp2.find("Last")) != -1):
                        last_date = temp2.split(':')[1].strip()
                    else:
                        status = 'Defective'
                except:
                    status = 'Under Scrutiny'

                temp1 = re.sub(r"\s+", " ", res1).strip()

                if ')' in temp1:
                    temp1 = temp1.split(')')
                else:
                    temp1 = temp1.split()

                if temp1[0][0].isdigit():
                    case_type = (temp1[-1]).strip().replace('(', ' ').replace(')', ' ')
                    case_number = temp1[0].split('/')[0].strip()
                    case_year = temp1[0].split('/')[1].strip()
                else:
                    case_type = (temp1[0]).strip().replace('(', ' ').replace(')', ' ')
                    case_number = temp1[1].split('/')[0].strip()
                    case_year = temp1[-1].split('/')[1].strip()
                
                for span_temp in tree.xpath('//span/text()'):
                    if 'Advocate' in span_temp:
                        advocate = span_temp.split(':')[1].strip()

                respondent = res3.strip() 
                respondent = re.sub('V.*?0', '', respondent)
                respondent = ('').join(respondent.split())
                respondent = re.sub('V.*?.', '', respondent)
                petitioner = res5.strip()
                import pdb; pdb.set_trace() 
                
                if((res4.find("Court")) != -1):
                    court_number = res4.split(':')[1].strip()
                else:
                    court_number = ''

                dict_case = {
                        "case_type": case_type,
                        "case_number": case_number,
                        "case_year": case_year,
                        "petitioner": petitioner,
                        "respondent": respondent,
                        "advocate": advocate
                }

                dict_court = {
                    "court_no": court_number,
                    "next_date": next_date,
                    "last_date": last_date,
                    "disposed_date": disposed_date,
                    "status": status 
                }

                dict_main = {
                    "case":dict_case,
                    "court_details":dict_court
                }

                js = json.dumps(dict_main)
                final_js = json.loads(js)
                final_js = json.dumps(final_js, indent=4, sort_keys=True)
            except:
                tb = traceback.format_exc()
                print(tb)
                import pdb; pdb.set_trace()

            with open('json_file.txt','a') as f:
                f.write(final_js)
                f.write('\n')

        print('{} th Page Successfully Scraped===='.format(page_count))
