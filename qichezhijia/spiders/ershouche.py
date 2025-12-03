import scrapy
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import json
from qichezhijia.items import QichezhijiaItem

class ErshoucheSpider(CrawlSpider):
    name = "ershouche"
    allowed_domains = ["che168.com", "cacheapigo.che168.com", "cacheapi.che168.com"]
    # 汽车列表
    start_urls = ["https://www.che168.com/china/a0_0msdgscncgpi1lto8cspexx0/#pvareaid=100943",
                  "https://www.che168.com/beijing/a0_0msdgscncgpi1lto8cspexx0/#pvareaid=104649",
                  "https://www.che168.com/chengdu/a0_0msdgscncgpi1lto8cspexx0/#pvareaid=104649"]

    # 配置页
    config_url = "https://cacheapigo.che168.com/CarProduct/GetParam.ashx?specid={}&callback=configTitle"
    config2_url = "https://cacheapi.che168.com/CarProduct/GetSpecListConfig.ashx?specid={}&callback=configContent"

    # 配置LinkExtractor
    # 详情页链接提取器
    detail_link_extractor = LinkExtractor(allow=r'.*/dealer/\d+/\d+\.html', restrict_xpaths=("//ul[@class='viewlist_ul']/li/a",))
    
    # 分页链接提取器 - 更精确的XPath选择器，只提取分页按钮
    pagination_link_extractor = LinkExtractor(
        restrict_xpaths=("//div[@id='listpagination']/a",),  # 分页容器下的所有链接
        allow=r'.*/a0_0msdgscncgpi\d+lto8cspexx0/.*',  # 确保只匹配分页链接
        deny=r'.*#.*'  # 排除包含#的链接，这些通常是页内锚点
    )

    # 爬取规则
    rules = (
        # 处理详情页数据
        Rule(detail_link_extractor, callback="parse_detail", follow=False),
        # 处理分页链接 - 自动跟进分页
        Rule(pagination_link_extractor, follow=True),
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
                    item = QichezhijiaItem()
                    item["specid"] = specid
                    yield scrapy.Request(detail_url, callback=self.parse_detail, meta={"specid": specid, "item": item})

    def parse_detail(self, response, **kwargs):
        # 从meta中获取specid和item
        specid = response.meta.get("specid")
        item = response.meta.get("item")
        
        if not item:
            item = QichezhijiaItem()

        item["target_url"] = response.url

        # 提取详情页数据
        self.get_detail_data(response, item)
            
        # 如果specid存在，请求配置页面
        if specid:
            # 拼接配置页面URL
            url = self.config_url.format(specid)
            # 请求配置页面，传递item和specid
            yield Request(url, callback=self.parse_config, meta={"item": item, "specid": specid})
            
            # 请求第二个配置页面
            url2 = self.config2_url.format(specid)
            yield Request(url2, callback=self.parse_config2, meta={"item": item, "specid": specid})
    
    def parse_config(self, response):
        # 从meta中获取item
        item = response.meta.get("item")
        specid = response.meta.get("specid")
        
        # 处理JSONP响应，去除callback函数名
        jsonp_text = response.text
        json_text = jsonp_text[jsonp_text.index('(') + 1 : jsonp_text.rindex(')')]
        
        # 解析JSON数据
        try:
            config_data = json.loads(json_text)
            
            # 更新item的配置数据
            self.analyze_config_data(config_data, item)
        except json.JSONDecodeError as e:
            print(f"解析配置数据失败: {e}")
        
        # 如果已经有配置2的数据，返回完整item
        if item.get("config2_data"):
            yield item
        else:
            # 否则暂时保存item，等待配置2的数据
            response.meta["item"] = item
    
    def parse_config2(self, response):
        # 从meta中获取item
        item = response.meta.get("item")
        
        # 处理JSONP响应，去除callback函数名
        jsonp_text = response.text
        json_text = jsonp_text[jsonp_text.index('(') + 1 : jsonp_text.rindex(')')]
        
        # 解析JSON数据
        try:
            config2_data = json.loads(json_text)

            # 更新item的配置2数据
            self.analyze_config2_data(config2_data, item)
            item["config2_data"] = True
        except json.JSONDecodeError as e:
            print(f"解析配置数据2失败: {e}")
            item["config2_data"] = False
        
        # 如果已经有配置1的数据，返回完整item
        if item.get("config_data"):
            yield item
        else:
            # 否则暂时保存item，等待配置1的数据
            response.meta["item"] = item
    
    def get_detail_data(self, response, item):
        # 解析详情页数据    
        # 提取class="all-basic-content fn-clear"下前三个ul的数据
        basic_content = response.xpath('//div[@class="all-basic-content fn-clear"]')
        ul_list = basic_content.xpath('./ul[position()<=3]')

        # 检查是否有足够的ul元素
        if ul_list:
            # 第一列
            li_items = ul_list[0].xpath('./li')
            # 第1个li：上牌时间
            if len(li_items) > 0:
                label = li_items[0].xpath('./span[@class="item-name"]/text()').get('')
                if label:
                    all_text = li_items[0].xpath('string(.)').get('')
                    item['shangpai_shijian'] = all_text.replace(label, '', 1).strip()

            # 第2个li：表显里程
            if len(li_items) > 1:
                label = li_items[1].xpath('./span[@class="item-name"]/text()').get('')
                if label:
                    all_text = li_items[1].xpath('string(.)').get('')
                    item['biaoxian_lichen'] = all_text.replace(label, '', 1).strip()

            # 第3个li：变速箱
            if len(li_items) > 2:
                label = li_items[2].xpath('./span[@class="item-name"]/text()').get('')
                if label:
                    all_text = li_items[2].xpath('string(.)').get('')
                    item['biansuxiang'] = all_text.replace(label, '', 1).strip()

            # 第4个li：排放标准
            if len(li_items) > 3:
                label = li_items[3].xpath('./span[@class="item-name"]/text()').get('')
                if label:
                    all_text = li_items[3].xpath('string(.)').get('')
                    item['pailiang_biaozhun'] = all_text.replace(label, '', 1).strip()

            # 第5个li：排量
            if len(li_items) > 4:
                label = li_items[4].xpath('./span[@class="item-name"]/text()').get('')
                if label:
                    all_text = li_items[4].xpath('string(.)').get('')
                    item['pailiang'] = all_text.replace(label, '', 1).strip()

            # 第6个li：发布时间
            if len(li_items) > 5:
                label = li_items[5].xpath('./span[@class="item-name"]/text()').get('')
                if label:
                    all_text = li_items[5].xpath('string(.)').get('')
                    item['fabu_shijian'] = all_text.replace(label, '', 1).strip()

    def analyze_config_data(self, config_data, item):
        if "result" not in config_data or not config_data["result"]:
            return

        if "paramtypeitems" not in config_data["result"]:
            return

        json_data = config_data["result"]["paramtypeitems"]

        # 基本参数
        if len(json_data) > 0 and len(json_data[0]["paramitems"]) > 4:
            item["chexing_name"] = json_data[0]["paramitems"][0]["value"]
            item["changshang_price"] = json_data[0]["paramitems"][1]["value"]
            item["changshang"] = json_data[0]["paramitems"][2]["value"]
            item["jibie"] = json_data[0]["paramitems"][3]["value"]
            item["nengyuan_type"] = json_data[0]["paramitems"][4]["value"]

    def analyze_config2_data(self, config2_data, item):
        if "result" not in config2_data or not config2_data["result"]:
            return

        if "configtypeitems" not in config2_data["result"]:
            return

        json_data = config2_data["result"].get("configtypeitems", [])

        # 被动安全
        if len(json_data) > 0 and len(json_data[0]["configitems"]) > 2:
            item["zhufu_qinang"] = json_data[0]["configitems"][0]["valueitems"][0]["value"]
            item["qianhou_qinang"] = json_data[0]["configitems"][1]["valueitems"][0]["value"]
            item["qianhou_tou_qinang"] = json_data[0]["configitems"][2]["valueitems"][0]["value"]
