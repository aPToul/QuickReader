#!/usr/bin/python
import re
import json
import tokenize
import os, os.path
from math import trunc

# For each article scraped, tokenizes the text and find word modifiers surrounding keywords (topics/objects of interest)
# A bag of words approach is used to score each keyword found and a summary is outputted to a text file


### Variable Initialization ###

# Number of webpages scraped (in this case, Bloomberg and Reuters)
webPageCount = 2

# Subfolders containing scraped web articles
folders = ["r", "b"]

# List of stop words for removal (list obtained from http://xpo6.com/list-of-english-stop-words/)
stp = []

# Stores all words (except stop words) in a given text file in the order they appear
sequence = []

# A static list of word modifiers which are buzzwords (words used in specific contexts, such as "plummeted")
# Assumes the average reader is only scanning for familiar buzzwords to quickly gather information
sent = []

# A list of potential keywords that can be modified, called "keywords"
# Eventually, replace this with a parser which automatically identifies subjects in a sentence
filtr = []

# Radius of how many words around a keyword a reader is assumed to read (before and after)
# Can be made dynamic based on how important a keyword / modifier pair is (i.e. how interested the reader is)
# Potential improvements include normalizing this by paragraph length (i.e. interest tapers off after a paragraph)
steps = 4

# A list of scores assigned to the buzzwords for scoring purposes
values = []


### Important data structures generated ###

# Index containing only keywords and word modifiers, made unique by their position
index = {}

# An adjacency list of the indexed keywords and their adjacent words in the index
adjlist = {}

# Scores given to each keyword in the adjacency list based off its surrounding word modifiers
scores = {}

# A dictionary which stores a list of all scores given to a keyword
superscores = {}


### Count the number of articles scraped ###

# Tracks the number of articles filtered for each webpage
articleCount = []

# Traverse each subfolder in the order given
k = 0
while (k < webPageCount):
	path, dirs, files = os.walk(folders[k]).next()
	# Count the number of files in a given subfolder
	file_count = len(files)
	# Each article has 4 files associated with it:
	# The header and body as text files and as jsons
	articleCount.append(file_count/4)
	k = k + 1


### Read in the lists of word types ###

# Folder containing the text files for stop words, keywords, word modifiers and the score 
wordbank = "readins/"

# Read in stop words
f = open(wordbank + "stop.txt", "r")
lst = f.read()
stp = lst.split()
f.close

# Read in keywords
f = open(wordbank + "filter.txt", "r")
lst = f.read()
filtr = lst.split()
f.close

# Read in modifier words, which are all buzzwords
f = open(wordbank + "sentiment.txt", "r")
lst = f.read()
sent = lst.split()
f.close

# Read in the sentiment (from 1 to 10) of buzzwords for scoring
# Note that sentiment values should be in the same order as their respective buzzword in sentiment.txt
f = open(wordbank + "values.txt", "r")
lst = f.read()
values = lst.split()
f.close


# Words that are for indexing: keywords and modifier words
ultra = []
ultra =  filtr + sent


### Procedure for tokenizing a document ###

# Tokenize and append words to the sequence
def handle_token(type, token, (srow, scol), (erow, ecol), line):
	if tokenize.tok_name[type] == "NAME":
		s = repr(token)
		# Basic data cleaning
		s = s.lower()
		s  = re.sub('\'', '', s)
		# Remove stop words
		if s not in stp:
			sequence.append(s)
	elif tokenize.tok_name[type] == "STRING":
		handle_string_token(repr(token))

def handle_token_level(type, token, (srow, scol), (erow, ecol), line):
	if tokenize.tok_name[type] == "NAME":
		s = repr(token)		
		s = s.lower
		sequence.append(s)

def handle_string_token(string):
	# Hack method for basic data cleaning
	fr = open("temp.txt", "w")
	fr.write(re.sub('[\']', '', string))
	fr.close
	fr = open("temp.txt", "r")

	tokenize.tokenize(fr.readline, handle_token_level)


### Procedure which indexes keywords and word modifiers in order ###
def build_index(ultra):
	x = 0
	for word in sequence:
		if word in ultra:
			if index.has_key(word):
				index[word].append(x)
			else:
				index[word] = []
				index[word].append(x)
			x += 1

### Procedure which generates a dictionary that stores words adjacent to keywords in the index ###
def build_adjacency_list(filtr):
	# A variable which keeps track of the current bucket in the index
	i = 0
	# For each keyword
	for word in filtr:
		if index.has_key(word):
			# For each case that the keyword is found
			for ind in index[str(word)]:
				# Make the dictionary key unique by appending the position of the keyword
				adjlist[str(word)+" "+str(ind)] = []

				# Define the maximum and minimum for adjacenct buckets
				start = max(ind-steps, 0)
				end = min(len(sequence), ind+steps)
				
				# Check for adjacent keywords to the left
				ambig = False
				for i in range(start, ind):
					if sequence[i] in filtr: 
						ambig = True
						break				
				
				# Having two keywords nearby is not handled well in a bag-of-words approach				
				# As a heuristic, return 1/2 as many words if a keyword is found (to the left)
				if ambig:
					start = trunc(max(ind-(steps/2), 0))

				# Append words to the left to the adjacency list for the given keyword
				# Words are made unique by position
				for i in range(start, ind):
					adjlist[str(word)+" "+str(ind)].append([sequence[i], i])

				ambig = False
				# Check for adjacent keywords to the right
				for i in range(ind + 1, end):
					if sequence[i] in filtr:
						ambig = True
						break				
				# As a heuristic, return 1/2 as many words if a keyword is found (to the right)
				if ambig:
					end = trunc(min(len(sequence), ind+(steps/2)))

				# Append words to the right to the adjacency list for the given keyword
				# Words are made unique by position
				for i in range(ind + 1, end):
					adjlist[str(word)+" "+str(ind)].append([sequence[i], i])

### Scoring algorithm ###
def score(adjlist, sent, values):
	scores = {}
	for key in adjlist:
		# The score and number of word modifiers found are defaulted to 0
		n = 0
		score = 0
		for pair in adjlist[key]:
			# Adjlist has two values per key: an adjacent word and its position
			# Obtain only the word to see if it is a word modifier
			adjWord = pair[0]
			
			if adjWord in sent:
				# Capture the sentiment value of the word modifier
				value = values[sent.index(adjWord)]
				# Add it to the score
				score = score +	int(value)
				n = n + 1
		if not n == 0:
			# Take the average score
			score = score/n
			scores[key] = score
	return scores



### Main Procedure ###

# For each website
k = 0
while k < webPageCount:
	folder = folders[k]
	
	# For each article
	for z in range(0, articleCount[k]):
		# Open the scraped article
		f = open(folder + "/" + str(z) + "_body.txt", "r+")
		body = f.readline

		# Tokenize the article
		tokenize.tokenize(f.readline, handle_token)
		f.close()
		
		# Build an "index" based on this tokenization
		# Only store important words (keywords and modifiers)
		build_index(ultra)

		# Build an adjacency list for keywords in the index
		build_adjacency_list(filtr)	

		# Score each keyword based on its adjacent word modifiers
		scores = {}
		scores = score(adjlist, sent, values)
		
		# Summarize results in a score dictionary which stores all contexts of a keyword
		for key in scores:
			# In the index, a word is made unique by appending its position after a space
			# Obtain the keyword only to tally together results for that word
			realKey = re.sub('[\']', '', key)
			temp = realKey.split(' ')
			realKey = temp[0]
			
			# Append the score found in this instance
			if superscores.has_key(realKey):
				superscores[realKey].append(scores[key])
			else:
				superscores[realKey] = []
				superscores[realKey].append(scores[key])

		# Clear dictionaries and the sequence list
		sequence = []
		adjlist = {}
		index = {}
		scores = {}

	k = k + 1

### Write results to a text file ###

f = open("score/scores.txt", "w")
for key in superscores:
	generator = ""
	for scr in superscores[key]:
		generator = generator + " " + str(scr)
	f.write(key + ":" + generator + "\n")
f.close
superscores = {}
