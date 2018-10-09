import re
import argparse
import scrapy
import scrapy.crawler
import scrapy.settings
import scrapy.pipelines.files
import loginform

base_site=''
login_url=''

class CustomFilesPipeline(scrapy.pipelines.files.FilesPipeline):
    """A custom file pipeline to avoid filenames based on hashing"""
    def file_path(self, request, response=None, info=None):
        media_guid = request.url.split('/')[-1]
        return f'{media_guid}'

    def get_media_requests(self, item, info):
        for file_url in item['file_urls']:
            yield scrapy.Request(
                file_url, headers=dict(Referer=base_site))


class ImgSpider(scrapy.Spider):
    name = 'imgspider'
    custom_settings = dict(
        ITEM_PIPELINES={f'{__name__}.CustomFilesPipeline': 1},
        SPIDER_MIDDLEWARES={
            'scrapy.spidermiddlewares.referer.RefererMiddleware': 100
        },
        FILES_STORE='/home/ide/git/web-crawlers/imgspider-results',
        DOWNLOAD_DELAY=1,
        AUTOTHROTTLE_ENABLED=True,
        AUTOTHROTTLE_START_DELAY=1)

    def __init__(self,
                 start='',
                 username='',
                 password='',
                 directory='',
                 newer=True,
                 older=False):
        self.start = start
        self.username = username
        self.password = password
        self.newer = newer
        self.older = older

    start_urls = [
        login_url
    ]

    def parse(self, response):
        data, url, method = loginform.fill_login_form(
            response.url,
            response.body,
            username=self.username,
            password=self.password)
        return scrapy.FormRequest(
            url, method=method, formdata=data, callback=self.after_login)

    def after_login(self, response):
        print('LOGGED IN')
        return scrapy.Request(self.start, callback=self.parse_images)

    def parse_images(self, response):
        print('PARSING IMAGES')
        next = []
        next.extend(response.css('.next a::attr(href)'))
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        current = response.css('.ui-scroll-view::attr(data-src)')
        try:
            pages = int(response.xpath(
                '//*[contains(concat( " ", @class, " " ), concat( " ", "work-info", " " ))]'
            ).re(r'(\d*)P')[0])
        except (ValueError, IndexError):
            pages = 1
        for img in current:
            for p in range(pages):
                for ending in ['.png', '.jpg']:
                    yield {
                        'file_urls': [
                            self.get_original_img_url(
                                response.urljoin(x), ending=ending, page=p)
                            for x in current.extract()
                        ]
                    }
        if not next:
            return
        for n in next:
            yield scrapy.Request(
                response.urljoin(n.extract()), callback=self.parse_images)

    def get_original_img_url(self, url, ending='.png', page=0):
        print(url, ending, page)
        return re.sub(r'/c.*(/img/.*_p).*?.jpg',
                      f'/img-original\\g<1>{page}{ending}', url)


def main():
    parser = argparse.ArgumentParser(
        description='Download images from a gallery')
    parser.add_argument('-s', '--start-url')
    parser.add_argument('-u', '--username')
    parser.add_argument('-p', '--password')
    parser.add_argument('-d', '--directory')
    parser.add_argument('-n', '--newer', action='store_true')
    parser.add_argument('-o', '--older', action='store_true')
    args = parser.parse_args()
    process = scrapy.crawler.CrawlerProcess(dict(FILES_STORE=args.directory))
    process.crawl(
        ImgSpider,
        start=args.start_url,
        username=args.username,
        password=args.password,
        newer=args.newer,
        older=args.older)
    process.start()


if __name__ == '__main__':
    main()
