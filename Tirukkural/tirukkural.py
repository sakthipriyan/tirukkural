# coding= utf-8
'''
Created on 26-Mar-2013

@author: sakthipriyan
'''
import sqlite3 as sqlite
import logging
from tirukkural.tweet import init_tweetbot, post_tweet_en, post_tweet_ta
from tirukkural.daemon import Daemon
import sys


database = '/var/opt/tirukkural/tirukkural.db'
log_file = '/var/log/tirukkural/service.log'
pid = '/var/run/tirukkural.pid'

def get_next_count():
    connection = None
    data = 1
    try:
        connection = sqlite.connect(database)
        cursor = connection.cursor()
        cursor.execute('SELECT value FROM application WHERE key = 1')
        data = cursor.fetchone()
        value = int(data[0])
        if value == 1330:
            new_value = 1
        else:    
            new_value = str(int(data[0]) + 1)
        cursor.execute('UPDATE application set value = ? WHERE key = ?',(new_value,1))
        connection.commit()
    except sqlite.Error, e:
        print ("Error %s:" % e.args[0])
    finally:
        if connection:
            connection.close()
    return value

def get_kurals(kural_id):
    connection = None
    data = None
    try:
        connection = sqlite.connect(database)
        cursor = connection.cursor()
        
        cursor.execute('SELECT * FROM kural_ta where id = ?',(kural_id,))
        data_ta = cursor.fetchone()
        
        cursor.execute('SELECT * FROM kural_en where id = ?',(kural_id,))
        data_en = cursor.fetchone()
        
        data = (data_ta,data_en)
    except sqlite.Error, e:
        print("Error %s:" % e.args[0])
    finally:
        if connection:
            connection.close()
    return data


def process_next_kural():
    count = get_next_count()
    data = get_kurals(count)
    if((int(count))%10 == 1):
        post_tweet_ta("பால்: %s\nஇயல்: %s\nஅதிகாரம்: %s" % (data[0][1],data[0][2],data[0][3]))    
        post_tweet_en("Section: %s\nChapterGroup: %s\nChapter: %s" % (data[1][1],data[1][2],data[1][3]))
    post_tweet_ta(u'குறள் ' + str(count) + ':\n' + data[0][4])
    post_tweet_en(u'Couplet ' + str(count) + ':\n' + data[1][4])
    post_tweet_ta(u'விளக்கம்: ' + data[0][5])
    post_tweet_en(u'Explanation: ' + data[1][5])
    
def service():
    init_logging()
    init_tweetbot()
    process_next_kural()
    
def init_logging():
    logging.basicConfig(level=logging.INFO, filename=log_file,
                        format='%(asctime)s [%(threadName)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    logging.info('-------------### Starting Tirukkural service ###-------------')


class TirukkuralDaemon(Daemon):
    def run(self):
        service()

if __name__ == "__main__":
    daemon = TirukkuralDaemon(pid)
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            init_logging()
            logging.info('-------------### Stopping Tirukkural service ###-------------')
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)