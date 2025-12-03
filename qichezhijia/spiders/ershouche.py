from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy import Request
import json


class ErshoucheSpider(CrawlSpider):
    name = "ershouche"
    allowed_domains = ["che168.com", "cacheapigo.che168.com", "cacheapi.che168.com"]
    # 汽车列表
    start_urls = ["https://www.che168.com/xiamen/a0_0msdgscncgpi1lto8cspexx0/#pvareaid=106289"]

    # 配置页
    config_url = "https://cacheapigo.che168.com/CarProduct/GetParam.ashx?specid={}&callback=configTitle"
    config2_url = "https://cacheapi.che168.com/CarProduct/GetSpecListConfig.ashx?specid={}&callback=configContent"

    r1 = LinkExtractor(restrict_xpaths=("//ul[@class='viewlist_ul']/a",))
    r2 = LinkExtractor(restrict_xpaths=("//div[@id='listpagination']/a",))

    # 在通过start_urls访问页面通过规则获取指定链接后，会继对链接进行请求，再返回Response 对象
    rules = (
        # follow 在访问链接对象回来后，是否再使用这个规则处理页面链接
        # 处理详情页数据
        Rule(r1, callback="parse_detail", follow=False),
        # 分页 follow,
        Rule(r2, follow=True),
    )

    def parse_start_url(self, response):
        # 首先处理列表页，获取所有汽车li元素的specid
        car_list = response.xpath("//ul[@class='viewlist_ul']/li")
        for car in car_list:
            # 获取specid属性
            specid = car.xpath("./@specid").get()
            if specid:
                # 获取详情页链接
                detail_url = car.xpath("./a/@href").get()
                if detail_url:
                    # 构造完整的详情页URL
                    if not detail_url.startswith("http"):
                        detail_url = "https://www.che168.com" + detail_url
                    # 将specid传递给详情页处理函数
                    yield Request(detail_url, callback=self.parse_detail, meta={"specid": specid})

    def parse_detail(self, response, **kwargs):
        # 从meta中获取specid
        specid = response.meta.get("specid")
        
        # 解析详情页数据
        title = response.xpath('//h3[@class="car-brand-name"]/text()').extract_first()
        lichen = response.xpath('//ul[@class="brand-unit-item fn-clear"]/li[1]/h4/text()').extract_first()
        shijian = response.xpath('//ul[@class="brand-unit-item fn-clear"]/li[2]/h4/text()').extract_first()
        pailiang = response.xpath('//ul[@class="brand-unit-item fn-clear"]/li[3]/h4/text()').extract_first()
        price = response.xpath('//span[@id="overlayPrice"]/text()').extract_first()
        
        if any([title, lichen, shijian, pailiang, price]):
            if title:
                title = title.strip()
            if lichen:
                lichen = lichen.strip()
            if shijian:
                shijian = shijian.strip()
            if pailiang:
                pailiang = pailiang.strip()
            if price:
                price = price.strip().replace('¥','')+'万'

            print(f"汽车信息: {title} == {lichen} == {shijian} == {pailiang} == {price}")
            
            # 创建主item
            main_item = {
                "title": title,
                "lichen": lichen,
                "shijian": shijian,
                "pailiang": pailiang,
                "price": price,
                "specid": specid,
                "config_data": None,
                "config2_data": None
            }
            
            # 如果specid存在，请求配置页面
            if specid:
                # 拼接配置页面URL
                url = self.config_url.format(specid)
                # 请求配置页面，将主item传递下去
                yield Request(url, callback=self.parse_config, meta={"main_item": main_item})
                
                # 请求第二个配置页面
                url2 = self.config2_url.format(specid)
                yield Request(url2, callback=self.parse_config2, meta={"main_item": main_item})
            else:
                # 如果没有specid，直接返回主item
                yield main_item
    
    def parse_config(self, response):
        # 从meta中获取主item
        main_item = response.meta.get("main_item")
        specid = main_item.get("specid")
        
        # 处理JSONP响应，去除callback函数名
        jsonp_text = response.text
        json_text = jsonp_text[jsonp_text.index('(') + 1 : jsonp_text.rindex(')')]
        
        # 解析JSON数据
        try:
            config_data = json.loads(json_text)
            print(f"配置信息(specid={specid}): {config_data}")
            
            # 更新主item的配置数据
            main_item["config_data"] = config_data
            
            # 如果已经有第二个配置数据，返回完整item
            if main_item.get("config2_data") is not None:
                yield main_item
            else:
                # 否则将主item传递给下一个请求
                url2 = self.config2_url.format(specid)
                yield Request(url2, callback=self.parse_config2, meta={"main_item": main_item})
        except json.JSONDecodeError as e:
            print(f"解析配置数据失败(specid={specid}): {e}")
            # 即使解析失败，也要继续请求第二个配置页面
            url2 = self.config2_url.format(specid)
            yield Request(url2, callback=self.parse_config2, meta={"main_item": main_item})
    
    def parse_config2(self, response):
        # 从meta中获取主item
        main_item = response.meta.get("main_item")
        specid = main_item.get("specid")
        
        # 处理JSONP响应，去除callback函数名
        jsonp_text = response.text
        json_text = jsonp_text[jsonp_text.index('(') + 1 : jsonp_text.rindex(')')]
        
        # 解析JSON数据
        try:
            config2_data = json.loads(json_text)
            print(f"配置信息2(specid={specid}): {config2_data}")
            
            # 更新主item的第二个配置数据
            main_item["config2_data"] = config2_data
            
            # 现在已经有了所有数据，返回完整item
            yield main_item
        except json.JSONDecodeError as e:
            print(f"解析配置数据2失败(specid={specid}): {e}")
            # 即使解析失败，也要返回已有的数据
            yield main_item

