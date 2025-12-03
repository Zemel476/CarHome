# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import csv
from itemadapter import ItemAdapter
from qichezhijia.items import QichezhijiaItem


class QichezhijiaPipeline:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        # 直接定义中文表头
        self.fieldnames = [
            "车型ID", "上牌时间", "表显里程", "变速箱", "排放标准", "排量", 
            "发布时间", "车型名称", "厂商指导价(元)", "厂商", "级别", 
            "能源类型", "主/副驾驶座安全气囊", "前/后排侧气囊", 
            "前/后排头部气囊(气帘)", "目标网址"
        ]

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            csv_file_path=crawler.settings.get("CSV_FILE_PATH", "ershouche_data.csv")
        )

    def open_spider(self, spider):
        # 强制写入表头，不管文件是否存在
        self.csvfile = open(self.csv_file_path, 'w', newline='', encoding='utf-8')  # 使用'w'模式覆盖文件
        self.writer = csv.DictWriter(self.csvfile, fieldnames=self.fieldnames)
        self.writer.writeheader()
        print(f"已创建CSV文件并写入表头: {self.fieldnames}")

    def close_spider(self, spider):
        self.csvfile.close()

    def process_item(self, item, spider):
        # 只处理 QichezhijiaItem
        if not isinstance(item, QichezhijiaItem):
            return item
        
        adapter = ItemAdapter(item)

        # 构造行数据，使用中文标题
        row_data = {
            "车型ID": adapter.get("specid", ""),
            "上牌时间": adapter.get("shangpai_shijian", ""),
            "表显里程": adapter.get("biaoxian_lichen", ""),
            "变速箱": adapter.get("biansuxiang", ""),
            "排放标准": adapter.get("pailiang_biaozhun", ""),
            "排量": adapter.get("pailiang", ""),
            "发布时间": adapter.get("fabu_shijian", ""),
            "车型名称": adapter.get("chexing_name", ""),
            "厂商指导价(元)": adapter.get("changshang_price", ""),
            "厂商": adapter.get("changshang", ""),
            "级别": adapter.get("jibie", ""),
            "能源类型": adapter.get("nengyuan_type", ""),
            "主/副驾驶座安全气囊": adapter.get("zhufu_qinang", ""),
            "前/后排侧气囊": adapter.get("qianhou_qinang", ""),
            "前/后排头部气囊(气帘)": adapter.get("qianhou_tou_qinang", ""),
            "目标网址": adapter.get("target_url", "")
        }

        # 写入CSV文件
        self.writer.writerow(row_data)
        print(f"完整数据已保存到CSV: {row_data}")
        
        return item
