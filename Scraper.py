#!/usr/bin/python
import newspaper
import tokenize
import json
import re
from django.utils.encoding import smart_str, smart_unicode
import textwrap

# This code scrapes articles from news websites and stores them into text files
# The Newspaper framework has known bugs

# Tokenizer
def handle_token(type, token, (srow, scol), (erow, ecol), line):
	if tokenize.tok_name[type] == "NAME" or tokenize.tok_name[type] == "STRING":
		if not dict1.has_key(repr(token)):
			dict1[repr(token)] = [] 
		s = str(srow) + "," + str(scol)
		dict1[repr(token)].append(s)

# Hack procedure for cleaning text
def cleanUpString(toClean):
	# Append the letter 'a' to the string to handle empty strings
	# Will be removed later since it is a stop word
	toClean = smart_str(toClean) + " a"
	
	# Get rid of characters which lead to interperting issues
	toClean = re.sub('[\(\)\{\}<>]', ' ', toClean)
	
	# Ignore case
	toClean = toClean.lower()
	# Retain alphanumeric and spaces only
	toClean = textwrap.dedent(re.sub(r'([^\s\w]|_)+', '', toClean))
	return toClean

# Number of webpages and their respective folders/domains
count = 2
folders = ["r", "b"]
urls = ["http://www.reuters.com/finance", "http://www.bloomberg.com/markets"]

# Words used to judge whether an article is clicked or not
# Currently limited to "keywords" (potential subjects)
types = ["filter"]
wordDict = {}
# Read in words
for wordType in types:
	f = open("readins/" + wordType + ".txt")
	temp = f.read().split('\n')
	wordDict[wordType] = temp
	f.close

# Keep track of articles found
prevFound = []

# For each website
k = 0
while k < count:
	# Number of articles stored
	q = 0
	# Number of scraping attempts
	x = 0		

	folder = folders[k]
	# Forget articles that have been previously cached
	news = newspaper.build(urls[k], memoize_articles=False)
	for article in news.articles:		
		validated = False

		article.download()
		article.parse()

		title = cleanUpString(article.title)
		body = cleanUpString(article.text)

		# If the article has not already been found
		if not title in prevFound:
			# Add to list of found titles
			prevFound.append(title)		
			
			# Filter articles that are too short	
			if not (len(title) < 5 or len(body) < 35):
				#  Look for filter words in title
				for word in wordDict['filter']:								
					regex = re.compile(r"\W" + word + "\W")

					if len(word) > 1 and regex.search(title):
						validated = True
						break
				
			# If the article is appropriate
			if validated == True:
				# Save title in a text file
				fr = open(folder + "/" + str(q) + "_headline.txt", "w")
				fr.write(title) 
				fr.close	
				# Save body in a text file
				fr = open(folder + "/" + str(q) + "_body.txt", "w")
				fr.write(body)
				fr.close	
				# Tokenize title; save in a text file
				dict1 = {}
				fr = open(folder + "/" + str(q) + "_headline.txt", "r+")
				f = open(folder + "/" + str(q) + "_headline.json", "w")
				tokenize.tokenize(fr.readline, handle_token)
				for key in dict1.keys():
					dict1[key].insert(0, len(dict1[key]))
					dict1[key].insert(0, folder + "_" + str(q))
				json.dump(dict1, f)	
				f.close()
				fr.close()
				# Tokenize body; save in a text file
				dict1 = {}				
				fr = open(folder + "/" + str(q) + "_body.txt", "r+")
				f = open(folder + "/" + str(q) + "_body.json", "w")
				tokenize.tokenize(fr.readline, handle_token)
				for key in dict1.keys():
					dict1[key].insert(0, len(dict1[key]))
					dict1[key].insert(0, folder + "_" + str(q))
				json.dump(dict1, f)
				f.close()
				fr.close()
				q += 1
		x += 1
		# Stop after 1500 attempts
		if x > 1500:
			break		
	k = k + 1