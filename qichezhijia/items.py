# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class QichezhijiaItem(scrapy.Item):
    # 车辆基本信息
    specid = scrapy.Field()  # 车型ID

    shangpai_shijian = scrapy.Field()  # 上牌时间
    biaoxian_lichen = scrapy.Field()  # 表显里程
    biansuxiang = scrapy.Field()  # 变速箱
    pailiang_biaozhun = scrapy.Field()  # 排放标准
    pailiang = scrapy.Field()  # 排量
    fabu_shijian = scrapy.Field()  # 发布时间

    # 第一个配置页面数据
    chexing_name = scrapy.Field()   # 车型名称
    changshang_price = scrapy.Field()   # 厂商指导价(元)
    changshang = scrapy.Field()   # 厂商
    jibie = scrapy.Field()   # 级别
    nengyuan_type = scrapy.Field()   # 能源类型

    # 第二个配置页面数据
    zhufu_qinang = scrapy.Field()   # 主/副驾驶座安全气囊
    qianhou_qinang = scrapy.Field()   # 前/后排侧气囊
    qianhou_tou_qinang = scrapy.Field()   # 前/后排头部气囊(气帘)

    # 目标网址
    target_url = scrapy.Field()

    # 配置项
    config_data = scrapy.Field()
    config2_data = scrapy.Field()
