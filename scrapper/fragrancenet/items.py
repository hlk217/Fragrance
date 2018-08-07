# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class FragrancenetItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
	user = Field()
	rating = Field()
	rateDate = Field()
	text = Field()
	helpful = Field()
	unhelpful = Field()
	product = Field()
	product_year = Field()
	product_type = Field()
	product_gender = Field()
	product_brand = Field() 
	product_image = Field()
	product_img_ids = Field()
	product_note = Field()
	product_usage = Field()
	product_price = Field()
	product_size = Field()
	