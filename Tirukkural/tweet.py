'''
Created on 26-Mar-2013

@author: sakthipriyan
'''
from twython import Twython
import urllib2, os, time
from ConfigParser import  RawConfigParser, NoSectionError, NoOptionError
import logging

twitter_en = None
twitter_ta = None

wait_time_index = -1;
tweet_file = '/var/opt/tirukkural/tweet.cfg'

def init_tweetbot():
    global twitter_en, twitter_ta
    if(not os.path.isfile(tweet_file)):    
        logging.info('Twitter configuration file not found')
        return
    try:
        config = RawConfigParser()
        config.read(tweet_file)
        twitter_en = Twython(twitter_token = config.get('TweetAuth_en','twitter_token'),
                          twitter_secret = config.get('TweetAuth_en','twitter_secret'),
                          oauth_token = config.get('TweetAuth_en','oauth_token'),
                          oauth_token_secret = config.get('TweetAuth_en','oauth_token_secret'))
        
        twitter_ta = Twython(twitter_token = config.get('TweetAuth_ta','twitter_token'),
                          twitter_secret = config.get('TweetAuth_ta','twitter_secret'),
                          oauth_token = config.get('TweetAuth_ta','oauth_token'),
                          oauth_token_secret = config.get('TweetAuth_ta','oauth_token_secret'))
        
    except NoSectionError, NoOptionError:
        logging.info('Twitter initialisation failed')

def post_tweet_en(text):
    global twitter_en
    post_tweets(twitter_en, text)

def post_tweet_ta(text):
    global twitter_ta
    post_tweets(twitter_ta, text)

def post_tweets(twitter, text):
    if(len(text) <= 140):
        post_tweet(twitter, text)
    else:
        split_array = text.split(' ')
        output_array = []
        output = ''
        for text in split_array:
            if len(output + text) > 136:
                output_array.append(output)
                output = text + ' '
            else:
                output = output + text + ' '
        output_array.append(output)
        size = len(output_array)
        count = 0
        for text in output_array:
            count = count + 1
            post_tweet(twitter, text + str(count)+'/'+str(size))
    
def post_tweet(twitter, text):
    processed = False
    print text
    while not processed:
        wait_for_internet()
        try:
            logging.info('Tweeting... '+ text)
            twitter.updateStatus(status=text)
            processed = True
        except Exception, e:
            logging.error(str(e))
            time.sleep(get_wait_time())

def get_wait_time():
    wait_time = (1,2,4,8,16,32,64,128)
    length = len(wait_time)
    global wait_time_index
    wait_time_index = wait_time_index + 1
    if wait_time_index == length:
        wait_time_index = 0
    return wait_time[wait_time_index]

def wait_for_internet():
    wait = True
    while wait:
        try:
            urllib2.urlopen('http://www.google.com',timeout=15)
            wait = False
        except Exception: 
            sleep_time = get_wait_time()
            time.sleep(sleep_time)
            wait = True