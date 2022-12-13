#!/usr/bin/env python3

# since this is a cron, full paths are necessary in the script!

from io import StringIO
from html.parser import HTMLParser

# currently this is a hard install, look at https://github.com/amueller/word_cloud and stackoverflow for help
from wordcloud import WordCloud
import sqlite3
import configparser
    
def wordcloud(con):
    # Generate a word cloud image
    cur = con.cursor()
    res = cur.execute("select description, text, type from memories")
    results = res.fetchall()
    cur.close()
    big_string = '' 
    for result in results:
        string = (' ').join(result)
        big_string = big_string + ' ' + string
    wordcloud_svg = WordCloud(background_color='red').generate(big_string).to_svg()
    f = open((root_dir + "static/wordcloud.svg"),"w+")
    f.write(wordcloud_svg )
    f.close()   
    
    return big_string 

def wordlist_to_freqdict(wordlist):
    wordfreq = [wordlist.count(p) for p in wordlist]
    return dict(list(zip(wordlist,wordfreq)))
    
def sort_freqdict(freqdict):
    aux = [(freqdict[key], key) for key in freqdict]
    aux.sort()
    aux.reverse()
    return aux    


def get_stopwords():
    stop_dict = {}
    with open(root_dir + 'etc/cron/stopwords.txt') as f:
        for line in f:
            stop_dict[line.rstrip()] = 1
    return stop_dict

root_dir = '/home/hbarnard/projects/mema/'
config = configparser.ConfigParser()
config.read((root_dir + "etc/mema.ini"))
con = sqlite3.connect(config['main']['db'], check_same_thread=False)

big_string = wordcloud(con)
wordlist = big_string.split()

stop_dict = get_stopwords()

wordfreq = []
worddict = {}
for w in wordlist:
    if w.lower() not in stop_dict:
        worddict[w.lower()] = wordlist.count(w)

f = open(config['main']['keyword_slot_file'],"w+")
for key in worddict:
    f.write(key + "\n")
f.close()


