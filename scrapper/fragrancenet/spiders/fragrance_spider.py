from scrapy import Spider, Request
from fragrancenet.items import FragrancenetItem
import re
import urllib.request 
import urllib.error
import os.path


#command to redirect the stardard output and error message
#nohup scrapy crawl fragrance_spider -o log.json -t json &> /Volumes/Hueyling/fragrance.log  &

class FragranceSpider(Spider):
	name = 'fragrance_spider'
	allowed_urls = ['https://www.fragrancenet.com/']
	start_urls = ['https://www.fragrancenet.com/fragrances']

	
	def parse(self, response):
		# Find the total number of pages in the result so that we can decide how many urls to scrape next
		Lst = response.xpath('//div[@class="pagination cf"]/a/@href').extract()
		lastpageNum = max ( map(lambda x: int(x), [ re.split("page=", x)[1] if len( re.split("page=", x) ) > 1 else '1' for x in Lst ] ) )
		
		# List comprehension to construct all the urls
		result_urls = ['https://www.fragrancenet.com/fragrances?page={}'.format(x) for x in range(1,lastpageNum+1)]
		# Yield the requests to different search result urls, 
		# using parse_result_page function to parse the response.
#		for url in result_urls[-2:]:
#		for url in result_urls[:1]:
		for url in result_urls:
			yield Request(url=url, callback=self.parse_result_page)	
	
	def parse_result_page(self, response):
		# This fucntion parses the search result page.
		# We are looking for url of the detail page.
		detail_urls = response.xpath('//div[@class="resultItem heightSync"]/section/a/@href').extract()
		
		print('=' * 50)
		# Yield the requests to the details pages, 
		# using parse_detail_page function to parse the response.
		for url in detail_urls:
			yield Request(url=url, callback=self.parse_detail_page)		


	def parse_detail_page(self, response):
		# This fucntion parses the product detail page.
		product = response.xpath('//span[@class="productTitle"]/text()').extract_first().strip()
		if product == "" :
			product = response.xpath('//h1[@class="brandTitle"]/text()').extract_first().strip()
		
		product_info = response.xpath('//ul[@class="notes cf"]//span[@class="right"]/text()').extract()
		product_brand = product_info[0]
		product_note = None
		product_year = None
		product_usage = None
		if len(product_info) == 4:
			product_note = product_info[1]
			product_year = product_info[2]
			product_usage = product_info[3]
		elif len(product_info) == 3:
			product_note = product_info[1]
			product_year = product_info[2]
			if product_year != 'N/A':
				try:
					int(product_year)
				except ValueError:
					product_note = None
					product_year = product_info[1]
					product_usage = product_info[2]
					try:
						int(product_year)
					except:
						product_note = product_info[1]
						product_usage = product_info[2]
						product_year = None
			else:
				product_year = None
			
		elif len(product_info) == 2:
			product_year = product_info[1]
			try:
				int(product_year)
			except ValueError:
				product_note = product_year
				product_year = None
				
		#product_desc = response.xpath('//div[@class="lpdesc"]').extract() #not sure why I can't get the value of this one.
		
		product_price = ','.join ( response.xpath('//div[@class="pricing"]/@data-price').extract() )
		product_size = ','.join( response.xpath('//div[@data-grouptype="SIZE"]/@data-dim-value').extract() )
		product_img_ids = ','.join( response.xpath('//div[@class="variantText"]/@data-sku').extract() )
		product_image = 'https:'+ response.xpath('//div[@id="productImageContainer"]/a[@id="desktopZoom"]/@href').extract_first()
		product_gender =  response.xpath('//span[@class="genderBar desktop"]/span/text()').extract_first().strip()
		product_type = response.xpath('//span[@class="linkless"]/text()').extract_first().strip()

		# This is for extracting product image################################		
		if product_image != 'https:':		
			try:
				full_file_name =  'img/' + re.split("\/", product_image)[-1]
				if ( not os.path.exists(full_file_name)):
					urllib.request.urlretrieve(product_image,full_file_name) #download img
			except urllib.error.HTTPError as err:
				if err.code == 404:
					pass
				else:
					raise
		######################################################################
		
		# The first 5 reviews are on the product details page so we have to
		# carry them to the review pages.
		
		first_reviews = response.xpath('//div[@class="reviewContain cf"]')
		
		if len(first_reviews) == 0:
			# If the product does not have any reviews, we just return.	
			item = FragrancenetItem()
			item['user'] = None
			item['rating'] = None
			item['rateDate'] = None
			item['text'] = None
			item['helpful'] = None
			item['unhelpful'] = None
			item['product'] = product
			item['product_type'] = product_type
			item['product_gender'] = product_gender
			item['product_brand'] = product_brand
			item['product_year'] = product_year
			item['product_image'] = product_image
			item['product_note'] = product_note
			item['product_usage'] = product_usage
			item['product_img_ids'] = product_img_ids
			item['product_price'] = product_price
			item['product_size'] = product_size
		
			yield item
			
			return
		else:
		# If there are less than 5 reviews, we just scrape/yield all of them and call it a day.
		# Extract each field from the review tag
					
			for review in first_reviews:
				user = review.xpath('.//p[@role="text"]/text()').extract_first()
				rateDate = review.xpath('.//p[@role="text"]/text()').extract()[1].strip()
				rating = review.xpath('.//div/@data-score').extract_first() 
				text = review.xpath('.//p[@class="text"]/text()').extract_first()
				
				helpfultext = review.xpath('.//p[@class="total clear"]/text()').extract_first()
				if len ( re.findall('\d+', helpfultext) ) == 0 :
					helpful = ""
					unhelpful = ""
				else :
					helpful, total = map ( lambda x:int(x), re.findall('\d+', helpfultext) )
					unhelpful = total - helpful
				

				item = FragrancenetItem()
				item['user'] = user
				item['rating'] = rating
				item['rateDate'] = rateDate
				item['text'] = text
				item['helpful'] = helpful
				item['unhelpful'] = unhelpful
				item['product'] = product
				item['product_type'] = product_type
				item['product_gender'] = product_gender
				item['product_brand'] = product_brand
				item['product_year'] = product_year
				item['product_image'] = product_image
				item['product_note'] = product_note
				item['product_usage'] = product_usage
				item['product_img_ids'] = product_img_ids
				item['product_price'] = product_price
				item['product_size'] = product_size
			
				yield item
				
			num_reviews = response.xpath('//p[@class="numRev"]/text()').extract_first()
			_, _, num_reviews = map(lambda x:int(x), re.findall('\d+', num_reviews) )
			if num_reviews > 5:
				# List comprehension to construct all the urls
				num_pages = num_reviews // 5 +1
				
				review_urls =  [ re.split('#', response.request.url)[0] + '?page={}'.format(x) for x in range(2,num_pages)]
				
				for url in review_urls:
					yield Request(url=url, meta={'product': product, 'product_type': product_type, 'product_gender': product_gender, 'product_brand': product_brand, 'product_year':product_year, 'product_image':product_image, 'product_note':product_note, 'product_usage':product_usage, 'product_img_ids':product_img_ids, 'product_price':product_price, 'product_size':product_size }, callback=self.parse_review_page)
		
		
	def parse_review_page(self, response):
		# Retrieve each following review page 
		
		product = response.meta['product']
		product_type = response.meta['product_type']
		product_gender = response.meta['product_gender']
		product_brand = response.meta['product_brand']
		product_year = response.meta['product_year']
		product_image = response.meta['product_image']
		product_note = response.meta['product_note']
		product_usage = response.meta['product_usage']
		product_img_ids = response.meta['product_img_ids']
		product_price = response.meta['product_price']
		product_size = response.meta['product_size']
		
		print('>' * 50)

		# Find all the review tags
		reviews = response.xpath('//div[@class="reviewContain cf"]')
		
		# Extract each field from the review tag
		for review in reviews:
			user = review.xpath('.//p[@role="text"]/text()').extract_first()
			rateDate = review.xpath('.//p[@role="text"]/text()').extract()[1].strip()
			rating = review.xpath('.//div/@data-score').extract_first() 
			text = review.xpath('.//p[@class="text"]/text()').extract_first()
			
			helpfultext = review.xpath('.//p[@class="total clear"]/text()').extract_first()
			if len ( re.findall('\d+', helpfultext) ) == 0 :
				helpful = ""
				unhelpful = ""
			else :
				helpful, total = map ( lambda x:int(x), re.findall('\d+', helpfultext) )
				unhelpful = total - helpful
			

			item = FragrancenetItem()
			item['user'] = user
			item['rating'] = rating
			item['rateDate'] = rateDate
			item['text'] = text
			item['helpful'] = helpful
			item['unhelpful'] = unhelpful
			item['product'] = product
			item['product_type'] = product_type
			item['product_gender'] = product_gender
			item['product_brand'] = product_brand
			item['product_year'] = product_year
			item['product_image'] = product_image
			item['product_note'] = product_note
			item['product_usage'] = product_usage
			item['product_price'] = product_price
			item['product_size'] = product_size
		
			yield item

		

