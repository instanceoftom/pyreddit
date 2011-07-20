"""crawlers"""

from pyreddit.core import RedditAgent
import gevent
from gevent.pool import Pool


class SampleRedditCrawler(object):

    def __init__(self, reddit_agent,pool_size=10):
        self.agent = reddit_agent
        self.pool = Pool(pool_size)

    
    def crawl_for_users(self,subreddit,after=None,page_limit=1,usernames=None):

        page_number = 0
        page = self.agent.get_subreddit(subreddit,after=after)
        usernames = {} if  usernames == None else usernames
        while page_number < page_limit and page:
            print "Processing Page #%s" % page_number
            for post in page.get_posts():
                self.pool.spawn(self.scan_thread_for_usernames,post=post,usernames=usernames)
                
            page_number = page_number+1
            print "Found %s usernames so far" % len(usernames)
            try:
                page = page.get_next_page()
            except:
                page = None
        self.pool.join()
        
        return usernames

    def scan_thread_for_usernames(self,*args,**kwargs):
        post = kwargs.get('post',None)
        usernames = kwargs.get('usernames',None)
        thread = post.get_thread()
        added_count = 0
        if thread.author not in usernames:
            try:
                #print "requesting info 1 %s" % (thread.author)
                user_info = self.agent.get_user_info(thread.author)
                usernames[thread.author]=user_info
            except:
                usernames[thread.author]=None
            added_count = added_count + 1
        
        usernames[post.author]

        for reply in thread.get_all_replies():
            if reply.author not in usernames:
                try:
                    #print "requesting info `` %s" % (reply.author)
                    user_info = self.agent.get_user_info(reply.author)
                    usernames[reply.author]=user_info
                except:
                    usernames[reply.author]=None
                added_count = added_count + 1
        print "\t+%s from %s" % (added_count,post.title)
        return usernames
