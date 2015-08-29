# coding=utf-8
'''
Created on 26-Mar-2013

@author: sakthipriyan
'''
import logging
import sys
import time
import codecs
import sqlite3 as sqlite
from twython import Twython
from ConfigParser import RawConfigParser

__cfg = '/var/opt/tirukkural/tirukkural.cfg'
__db = '/var/opt/tirukkural/tirukkural.db'
__log = '/var/log/tirukkural/tirukkural.log'
__pid = '/var/run/tirukkural.pid'

class TirukkuralDaemon(object):
    def __init__(self,config,database):
        self.__config = config
        self.__database = database

    def run(self):
        logging.debug('------------###-------------')
        config = RawConfigParser()
        config.readfp(codecs.open(self.__config, "r", "utf8"))
        while True:
            self.process_kurals(config)
            # Time taken to tweet 1330 Tirukkural in 365 days.
            time.sleep(23711)

    def process_kurals(self, config):
        kural_id = self.get_next_count()
        languages = config.sections()
        for language in languages:
            kural = self.process_kural(language, kural_id, config)

    def process_kural(self,language, kural_id, config):
        twitter_token = config.get(language,'twitter_token')
        twitter_secret = config.get(language,'twitter_secret')
        oauth_token = config.get(language,'oauth_token')
        oauth_token_secret = config.get(language,'oauth_token_secret')
        label_couplet = config.get(language,'label_couplet')
        label_explanation = config.get(language,'label_explanation')
        label_section = config.get(language,'label_section')
        label_chapter_group = config.get(language,'label_chapter_group')
        label_chapter = config.get(language,'label_chapter')

        data = self.get_kural(language, kural_id)
        twitter = Twython(twitter_token, twitter_secret, oauth_token, oauth_token_secret)
        if((int(kural_id))%10 == 1):
            messages = [u"%s: %s\n%s: %s\n%s: %s" % (label_section,data[1],label_chapter_group,data[2],label_chapter,data[3])]
            self.post_to_twitter(twitter, messages)
        kural = u'%s %s:\n%s' % (label_couplet, kural_id, data[4])
        porul = u'%s:\n%s' % (label_explanation, data[5])
        messages = [kural,porul]
        self.post_to_twitter(twitter, messages)

    def post_to_twitter(self, twitter, messages):
        tweets = self.get_tweets(messages)
        last_id = None
        for tweet in tweets:
            response = twitter.update_status(status = tweet, in_reply_to_status_id = last_id)
            last_id = response['id']

    def get_tweets(self,messages):
        tweets = []
        for message in messages:
            if(len(message) > 140):
                count = 0
                words = message.split(' ')
                tweet = u''
                for word in words:
                    if len(tweet + word) < 135:
                        tweet = tweet + word + ' '
                    else:
                        count = count + 1
                        tweets.append(tweet + str(count))
                        tweet = word + ' '
                if tweet != '':
                    count = count + 1
                    tweets.append(tweet + str(count))
            else:
                tweets.append(message)
        return tweets

    def get_kural(self, language, kural_id):
        connection = None
        data = None
        try:
            connection = sqlite.connect(self.__database)
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM kural_'+language+' where id = ?',(kural_id,))
            data = cursor.fetchone()
        except sqlite.Error, e:
            logging.info("Error %s:" % e.args[0])
        finally:
            if connection:
                connection.close()
        return data

    def get_next_count(self):
        connection = None
        kural_id = 1
        try:
            connection = sqlite.connect(self.__database)
            cursor = connection.cursor()
            cursor.execute('SELECT value FROM application WHERE key = 1')
            data = cursor.fetchone()
            kural_id = int(data[0])
            if kural_id == 1330:
                next_kural = 1
            else:
                next_kural = str(kural_id + 1)
            cursor.execute('UPDATE application set value = ? WHERE key = ?',(next_kural,1))
            connection.commit()
        except sqlite.Error, e:
            logging.error("Error %s:" % e.args[0])
        finally:
            if connection:
                connection.close()
            logging.info("Tirukkural " + str(kural_id) + " will be tweeted")
        return kural_id

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename=__log,
                            format='%(asctime)s %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    daemon = TirukkuralDaemon(__cfg, __db)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            logging.info('-------------### Starting Tirukkural service ###-------------')
            daemon.run()
        elif 'stop' == sys.argv[1]:
            logging.info('-------------### Stopping Tirukkural service ###-------------')
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            logging.info('-------------### Restarting Tirukkural service ###-------------')
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
