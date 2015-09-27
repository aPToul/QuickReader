#!/usr/bin/python
import re
import json
import tokenize
import os, os.path
from math import trunc

# This code tokenizes a text file and finds word modifiers surrounding words of interest
# A naive scoring algorithm is implemented for initial testing


### Variable Initialization ###

# Number of webpages and their respective folders/domains
webPageCount = 2

# Name of subfolders for web articles scraped
folders = ["r", "b"]


# List of stop words for removal (stop word list from http://xpo6.com/list-of-english-stop-words/ )
stp = []

# All non stop-words in a text file and their positions
sequence = []

# Assuming the reader is not taking the time to understand a sentence, use a bag-of-words inspired approach
# Goal: find word modifiers around a word and use that to determine sentiment

# A list of word-modifiers
# Assumes the average reader is only looking for specific buzzwords when reading
sent = []

# A list of potential subjects that can be modified, called "keywords"
# For now, only judge a specific set of words from a topic
# Evetually, replace with a NLP technique which identifies subjects in a sentence
filtr = []

# Radius of how many words around a keyword a reader is assumed to read (before and after)
# Eventually should be dynamic based on how strong a word modifier is (i.e. how interested the reader is)
# Eventually should be paragraph-length depenendent (i.e. interest tapers off after a paragraph)
steps = 4

# A list of scores assigned to word modifiers for a naive scoring algorithm
values = []



### Data structures generated ###

# Index of keywords and word modifiers, made unique by their position
index = {}

# An adjacency list of keywords and their adjacent words, based off the above index
# Can contain a word in multiple positions
adjlist = {}

# Scores given to each keyword in the adjacency list based off its surrounding word modifiers
# Can contain a word in multiple positions
scores = {}



### Count the number of articles scraped ###

# Tracks the number of articles filtered for each webpage
articleCount = []

# Go to each subfolder in the order given
k = 0
while (k < webPageCount):
	path, dirs, files = os.walk(folders[k]).next()
	# Count the number of files in a given subfolder
	file_count = len(files)
	articleCount.append(file_count/4)
	k = k + 1


### Read in the lists of word types ###

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

# Read in modifier words
f = open(wordbank + "sentiment.txt", "r")
lst = f.read()
sent = lst.split()
f.close

# Words that are for indexing: keywords and modifier words
ultra = []
ultra =  filtr + sent

# Read in values of word modifiers for scoring
f = open(wordbank + "values.txt", "r")
lst = f.read()
values = lst.split()
f.close

# A place to store all scores computed for a given keyword
superscores = {}


### Procedure for tokenizing a document ###

# Tokenize and append words to the sequence
# Information about which word belongs to a given sentence is lost
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
	# Hack way for basic data cleaning
	fr = open("temp.txt", "w")
	fr.write(re.sub('[\']', '', string))
	fr.close
	fr = open("temp.txt", "r")

	tokenize.tokenize(fr.readline, handle_token_level)


### Procedure indexing keywords and word modifiers by their position ###
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

### Procedure which stores adjacent words to all keywords in a dictionary ###
def build_adjacency_list(filtr):
	# A variable which keeps track of the current bucket in the above word sequence
	i = 0
	for word in filtr:
		if index.has_key(word):
			for ind in index[str(word)]:
				adjlist[str(word)+" "+str(ind)] = []

				start = max(ind-steps, 0)
				end = min(len(sequence), ind+steps)
				
				# Check for adjacent keywords to the left
				ambig = False
				for i in range(start, ind):
					if sequence[i] in filtr: 
						ambig = True
						break				
				
				# Having two keywords nearby is not handled well in this bag-of-words approach				
				# As a heuristic, return 1/2 as many words if a keyword is found (to the left)
				if ambig:
					start = trunc(max(ind-(steps/2), 0))

				# Append words to the left
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

				# Append words to the right
				for i in range(ind + 1, end):
					adjlist[str(word)+" "+str(ind)].append([sequence[i], i])

### Naive scoring algorithm ###
def score(adjlist, sent, values):
	scores = {}
	for key in adjlist:
		n = 0
		score = 0
		for pair in adjlist[key]:
			# Adjlist has two values per key: the word and its position
			adjWord = pair[0]
			# Check if each adjacent word is a word modifier
			if adjWord in sent:
				# Capture the value of the word modifier
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
	q = 0
	x = 0		
	folder = folders[k]

	# For each article
	for z in range(0, articleCount[k]):
		f = open(folder + "/" + str(z) + "_body.txt", "r+")
		body = f.readline

		# Tokenize the article
		tokenize.tokenize(f.readline, handle_token)
		f.close()
		
		# Build an index based on this tokenization
		# Only store important words (keywords and modifiers)
		build_index(ultra)

		# Build an adjacency list for keywords based on this index
		build_adjacency_list(filtr)	

		# Score each filter word based on its adjacent word modifiers
		scores = {}
		scores = score(adjlist, sent, values)
		
		# Summarize results into a score dictionary
		for key in scores:
			realKey = re.sub('[\']', '', key)
			temp = realKey.split(' ')
			# In the index, a word is considered unique in each place it appears
			# Obtain the keyword only to tally together results for that word
			realKey = temp[0]
			
			# Append score to the keyword modified
			if superscores.has_key(realKey):
				superscores[realKey].append(scores[key])
			else:
				superscores[realKey] = []
				superscores[realKey].append(scores[key])

		sequence = []
		adjlist = {}
		index = {}
		scores = {}

	k = k + 1

### Write results to a text file ###

f = open("score/scores.txt", "w")
# Summarize results
for key in superscores:
	generator = ""
	for scr in superscores[key]:
		generator = generator + " " + str(scr)
	f.write(key + ":" + generator + "\n")
f.close
superscores = {}