# coding=utf-8
'''
Created on 26-Mar-2013

@author: sakthipriyan
'''
import sqlite3 as sqlite
import logging
from daemon import Daemon
import sys
import time
from twython_service.twython_service import TwythonService

__log_file = '/var/log/tirukkural/service.log'
__pid = '/var/run/tirukkural.pid'

class TirukkuralDaemon(Daemon):

    def run(self):
        self.database = '/var/opt/tirukkural/tirukkural.db'
        logging.debug('Running Tirukkural service')
        self.twyServiceEn = TwythonService('/var/opt/tirukkural/tweet_en.cfg', '/var/opt/tirukkural/tweet_en.db')
        self.twyServiceTa = TwythonService('/var/opt/tirukkural/tweet_ta.cfg', '/var/opt/tirukkural/tweet_ta.db')
        
        while True:
            self.process_kural()
            #Time taken to tweet 1330 Tirukkural in 365 days.  
            time.sleep(23711)

    def get_next_count(self):
        connection = None
        value = 1
        try:
            connection = sqlite.connect(self.database)
            cursor = connection.cursor()
            cursor.execute('SELECT value FROM application WHERE key = 1')
            data = cursor.fetchone()
            value = int(data[0])
            logging.info("Tirukkural " + str(value) + " will be tweeted")
            if value == 1330:
                new_value = 1
            else:    
                new_value = str(int(data[0]) + 1)
            cursor.execute('UPDATE application set value = ? WHERE key = ?',(new_value,1))
            connection.commit()
        except sqlite.Error, e:
            logging.error("Error %s:" % e.args[0])
        finally:
            if connection:
                connection.close()
        return value
    
    def get_kurals(self,kural_id):
        connection = None
        data = None
        try:
            connection = sqlite.connect(self.database)
            cursor = connection.cursor()
            
            cursor.execute('SELECT * FROM kural_ta where id = ?',(kural_id,))
            data_ta = cursor.fetchone()
            
            cursor.execute('SELECT * FROM kural_en where id = ?',(kural_id,))
            data_en = cursor.fetchone()
                    
            data = (data_ta,data_en)
        except sqlite.Error, e:
            logging.info("Error %s:" % e.args[0])
        finally:
            if connection:
                connection.close()
        return data
    
    def process_kural(self):
        count = self.get_next_count()
        data = self.get_kurals(count)
        if((int(count))%10 == 1):
            self.twyServiceTa.new_tweet(u"பால்: %s\nஇயல்: %s\nஅதிகாரம்: %s" % (data[0][1],data[0][2],data[0][3]))    
            self.twyServiceEn.new_tweet(u"Section: %s\nChapterGroup: %s\nChapter: %s" % (data[1][1],data[1][2],data[1][3]))
        self.twyServiceTa.new_tweet(u'குறள் ' + str(count) + ':\n' + data[0][4])
        self.twyServiceEn.new_tweet(u'Couplet ' + str(count) + ':\n' + data[1][4])
        self.twyServiceTa.new_tweet(u'விளக்கம்: ' + data[0][5])
        self.twyServiceEn.new_tweet(u'Explanation: ' + data[1][5])

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, filename=__log_file,
                            format='%(asctime)s %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    daemon = TirukkuralDaemon(__pid)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            logging.info('-------------### Starting Tirukkural service ###-------------')
            daemon.start()
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
