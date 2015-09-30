# QuickReader
I'm really interested in natural language processing and human behaviour.

I saw a lot of news being skimmed during my time on TD's Trading Floor in Toronto and wondered how much information was really being processed.

This project is an experiment I made to see what happens when someone only reads jargon (buzzwords used in a specific context) and associates them with the nearest topics.

INPUTS

Keywords and stop words are stored in filter.txt and stop.txt;
Word modifiers and their assumed meaning are stored in sentiment.txt and values.txt;
The articles are scraped automatically from any news website.

CODE SUMMARY

Scraper.py pulls articles from Bloomberg and Reuters using the Newspaper framework. At first, a lot of strange links were being scraped, so articles that did not contain any keywords (topics of interest) were removed.

ReadingAlgorithm.py tokenizes the text in each article and stores keywords and word modifiers in an index. For each keyword in the index, surrounding modifiers are stored in an adjacency list. Each keyword is then scored based on the sentiment of its nearby words.

