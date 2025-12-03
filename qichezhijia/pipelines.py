# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class QichezhijiaPipeline:
    def process_item(self, item, spider):
        # 打印接收到的数据
        print("\n" + "="*50)
        print(f"从 {spider.name} 接收到的数据:")
        print("="*50)
        print(item)
        print("="*50 + "\n")
        
        return item
