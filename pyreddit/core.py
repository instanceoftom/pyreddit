"""reddit"""

import json
import mechanize

vote_url = 'http://www.reddit.com/api/vote/'
vote_post_string = 'id=%s&dir=%s&r=%s&uh=%s'



class RedditThing(object):

	ups = 0
	downs = 0

	def __init__(self,json_data,reddit_agent=None):

		self._agent = reddit_agent
		self._data = json_data.get("data",{})

		for key,value in self._data.items():
			setattr(self,key,value)
	
	def set_vote(self,direction):
		vote_response = self._agent.set_vote(self.name,self.subreddit,direction)
		self._last_vote_response = vote_response

	def __str__(self):
		return self.__unicode__()

	def __unicode__(self):
		return u"RedditThing<%s> by %s" % (self.name,self.author)

class RedditT5(RedditThing):


	def __init__(self,json_data,reddit_agent=None):

		self._kind = json_data.get("kind","t5")
		super(RedditT5,self).__init__(json_data,reddit_agent)

	def get_as_subreddit(self):
		display_name = self.display_name
		return self._agent.get_subreddit(display_name)


class RedditComment(RedditThing):

	ups = 0
	downs = 0

	def __init__(self,json_data,reddit_agent=None):

		self._kind = json_data.get("kind","t1")
		self._replies = None
		super(RedditComment,self).__init__(json_data,reddit_agent)
	
	def get_replies(self):

		if self._replies:
			return self._replies

		try:
			children = self._data.get("replies",{}).get("data",{}).get("children",[])
		except:
			return [] # add logging
		replies = []

		for item in children:
			kind = item.get("kind",None)
			if kind == "t1":
				try:
					replies.append(RedditComment(item,self._agent))
				except:
					pass # add logging?
		self._replies = replies
		return replies

	def get_thread(self):
		return self._agent.get_permalinked_thread(self.name,self.permalink)

	def __unicode__(self):
		return u"RedditComment<%s> by %s" % (self.name,self.author)


	
class RedditPost(RedditThing):

	ups = 0
	downs = 0

	def __init__(self,json_data,reddit_agent=None):

		self._kind = json_data.get("kind","t3")
		super(RedditPost,self).__init__(json_data,reddit_agent)
	
	def get_thread(self):
		return self._agent.get_permalinked_thread(self.name,self.permalink)

	def __unicode__(self):
		return u"RedditPost<%s> by %s" % (self.name,self.author)


class RedditListing(RedditThing):

	def __init__(self,name,json_data,reddit_agent=None):

		self._name = name
		self._posts = None
		super(RedditListing,self).__init__(json_data,reddit_agent)

		for key,value in self._data.items():
			setattr(self,key,value)

	def get_posts(self):

		if self._posts:
			return self._posts

		children = self.children
		posts = []
		for item in children:
			kind = item.get("kind",None)
			if kind == "t3":
				try:
					posts.append(RedditPost(item,self._agent))
				except:
					pass # add logging?
		self._posts = posts
		return posts

	def get_last_post(self):
		try:
			return self.get_posts()[-1]
		except IndexError:
			return None


	def __unicode__(self):
		return u"RedditListing<%s>" % (self._name.title())

class RedditSubredditList(RedditListing):
	

	def __init__(self,json_data,reddit_agent=None):

		self._subreddits = None
		super(RedditSubredditList,self).__init__("List of reddits",json_data,reddit_agent)

		for key,value in self._data.items():
			setattr(self,key,value)


	def get_subreddits(self):
		
		if self._subreddits:
			return self._subreddits

		children = self.children
		subreddits = []
		for item in children:
			kind = item.get("kind",None)
			if kind == "t5":
				try:
					subreddits.append(RedditT5(item,self._agent))
				except:
					pass # add logging?
		self._subreddits = subreddits
		return subreddits


	def get_next_page(self):

		last_subreddit = self.get_subreddits()[-1]
		last_subreddit_name = last_subreddit.name

		return self._agent.get_subreddit_listing(after=last_subreddit_name)

class RedditSubreddit(RedditListing):

	_url = "http://www.reddit.com/r/%s/.json"
	
	def __init__(self,subreddit,json_data,reddit_agent=None):

		self.subreddit = subreddit
		self._kind = json_data.get("kind","t2")
		super(RedditSubreddit,self).__init__(subreddit,json_data,reddit_agent)

	def get_next_page(self):

		last_post = self.get_last_post()
		last_post_name = last_post.name

		return self._agent.get_subreddit(self.subreddit,after=last_post_name)


	def __unicode__(self):
		return u"RedditSubreddit<%s>" % (self.subreddit.title())

class RedditThread(RedditThing):

	_url = "http://www.reddit.com/r/%s/comments/%s.json"

	def __init__(self,name,json_data,reddit_agent=None):

		self.name = name
		self._kind = json_data[1]['kind']
		self._replies = None

		post_data = json_data[0].get('data',{}).get('children')[0]
		self.post = RedditPost(post_data,reddit_agent)

		self._reply_data = json_data[1]['data']['children']
		super(RedditThread,self).__init__(post_data,reddit_agent)
	
	def set_vote(self,direction):
		vote_response = self.post.set_vote(direction)
		self._last_vote_response = vote_response

	def get_replies(self):

		if self._replies:
			return self._replies

		try:
			children = self._reply_data
		except:
			return [] #add logging
		replies = []

		for item in children:
			kind = item.get("kind",None)
			if kind == "t1":
				try:
					a_reply = RedditComment(item,self._agent)
					a_reply.permalink = "%s%s" % (self.post.permalink,a_reply.id)
					replies.append(a_reply)
				except:
					pass # add logging?
		self._replies = replies
		return replies
	
	def get_all_replies(self,reply=None,replies=None):
		if replies == None:
			replies = set()
		
		if reply == None:
			target = self
		else:
			target = reply

		target_replies = target.get_replies()
		for target_reply in target_replies:

			replies.update(self.get_all_replies(reply=target_reply,replies=replies))
			replies.add(target_reply)
		
		replies.add(target)
		return replies




	
	def __unicode__(self):
		return u"RedditThread<%s>" % (self.name.title())

class RedditUserInfo(RedditThing):

	_url = "http://www.reddit.com/user/%s/about.json"

	def __init__(self,json_data,reddit_agent=None):

		self._kind = json_data.get("kind","t2")
		super(RedditUserInfo,self).__init__(json_data,reddit_agent)

	def __unicode__(self):
		return u"RedditUserInfo<%s> %s" % (self.id,self.name)

class RedditUserPage(RedditListing):

	_url = "http://www.reddit.com/user/%s.json"
	
	def __init__(self,username,json_data,reddit_agent=None,section=None):

		self.username = username
		self._kind = json_data.get("kind","t2")
		self._comments = None
		self._section = section if section else "overview"
	
		super(RedditUserPage,self).__init__(username,json_data,reddit_agent)

	def get_user_info(self):
		return self._agent.get_user_info(self.username)

	def get_comments(self):

		if self._comments:
			return self._comments

		#No comments in this section
		if self._section == "submitted":
			self._comments = []
			return self._comments

		children = self._data.get("children",{})
		comments = []

		for item in children:
			kind = item.get("kind",None)
			if kind == "t1":
				try:
					comments.append(RedditComment(item,self._agent))
				except:
					pass # add logging?
		self._comments = comments
		return comments

	def get_posts(self):

		if self._section == "comments":
			if self._posts:
				return self._posts
			else:
				self._posts = []
				return self._posts
		else:
			return super(RedditUserPage,self).get_posts()

	def get_last_comment(self):
		try:
			return self.get_comments()[-1]
		except IndexError:
			return None


	def get_last_item(self):

		last_post = self.get_last_post()
		last_comment = self.get_last_comment()

		if last_post == None:
			return last_comment
		if last_comment == None:
			return last_post
		
		#if self.filter == "newest"
		if last_post.created < last_comment.created:
			return last_post
		else:
			return last_comment

	def get_next_page(self):

		try:
			last_item = self.get_last_item()

			if not last_item:
				return None

			last_item_name = last_item.name

			return self._agent.get_user_page(self.username,after=last_item_name)
		except Exception as e:
			print e #add logging?
			return None

	def __unicode__(self):
		return u"RedditUserPage<%s>" % (self.username.title())

class RedditSession(object):

	_opener = None
	_username = 'a_test_account'
	_password = 'a_test_password'

	_login_url = 'http://www.reddit.com/api/login/'
	_login_post_string = 'user=%s&passwd=%s&api_type=json'
	
	#_subreddit_url = 'http://www.reddit.com/r/%s.json'

	_last_modhash = ''
	
	def __init__(self,**kwargs):
		#self._opener = kwargs.get('opener',None)

		self._username = unicode(kwargs.get('user',RedditSession._username))
		self._passwd = unicode(kwargs.get('passwd',RedditSession._password))
		print self._username
		print self._passwd
		self._cookies = mechanize.CookieJar()
		self._opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(self._cookies))

		self._do_login()

	
	def _do_login(self):

		post_data = RedditSession._login_post_string % (self._username,self._passwd)

		login_response = self.make_request(RedditSession._login_url,post_data,reqtype="login")

		self._login_response = login_response

		self.login_status = "Valid"


	def is_logged_in(self):
		return hasattr(self,"_login_modhash") and self._login_modhash != "" and self.login_modhash != None


	def make_request(self,url,post=None,reqtype=None):
		
		if post:
			response = self._opener.open(url,post)
		else:
			response = self._opener.open(url)
		
		json_data = json.load(response)

		if json_data:
			self._last_modhash = self.extract_modhash(json_data,reqtype=reqtype)
			self._last_response = json_data
		
		return json_data

	def extract_modhash(self,json_data,reqtype=None):
		
		if reqtype == None:
			pass #meh
		elif reqtype == "login":
			modhash= json_data.get('json',{}).get('data',{}).get('modhash',None)
			self._login_modhash = modhash
			return modhash
		elif reqtype == "user_page":
			return json_data.get('data',{}).get('modhash',None)

	def __unicode__(self):
		return u"RedditSession<%s> %s" % (self._login_modhash,self._username)

class RedditAgent(object):

	_after_pattern = "?after=%s"
	_user_info_cache = {}
	
	def __init__(self,reddit_session):
		
		self._session = reddit_session
		self._username = reddit_session._username

	def set_vote(self,name,subreddit,direction):
		
		modhash = self._session._login_modhash
		vote_request = vote_post_string % (name,direction,subreddit,modhash)
		vote_response = self._session.make_request(vote_url,vote_request,reqtype="vote")

		self._last_vote_response = vote_response

		return vote_response

	def get_subreddit(self,subreddit,after=None):

		url = RedditSubreddit._url % subreddit

		if after:
			url = "%s%s" % (url,self._after_pattern % (after,),)

		data = self._session.make_request(url,reqtype="basic_info")

		if data:
			return RedditSubreddit(subreddit,data,self)

	def get_subreddit_listing(self,after=None):

		url = "http://www.reddit.com/reddits.json"

		if after:
			url = "%s%s" % (url,"?after=%s"%after)
		
		print url
		data = self._session.make_request(url,reqtype="subreddit_listing")

		if data:
			return RedditSubredditList(data,self)

	def get_thread(self,subreddit,name,after=None):

		url = RedditThread._url % (subreddit,name)

		if after:
			url = "%s%s" % (url,self._after_pattern % (after,),)
		

		data = self._session.make_request(url,reqtype="thread")

		if data:
			return RedditThread(name,data,self)
	
	def get_permalinked_thread(self,name,permalink,after=None):
		
		url = "http://www.reddit.com%s.json" % permalink
				
		if after:
			url = "%s%s" % (url,self._after_pattern % (after,),)

		data = self._session.make_request(url,reqtype="permalink_thread")	


		if data:
			return RedditThread(name,data,self)

	def get_user_info(self,username,update=True):

		if username not in self._user_info_cache or update:
			data = self._session.make_request(RedditUserInfo._url % username,reqtype="basic_info")
			if data:
				user =RedditUserInfo(data,self)
			else:
				user = None
			self._user_info_cache[username] = user	
		else:
			user = self._user_info_cache[username]
		
		return user



	def get_user_page(self,username,after=None):

		url = RedditUserPage._url % username

		if after:
			url = "%s%s" % (url,self._after_pattern % (after,),)

		data = self._session.make_request(url,reqtype="user_page")

		if data:
			return RedditUserPage(username,data,self)

	def get_my_user_page(self,after=None):

		if self._username:
			return self.get_user_page(self.username,after=after)

	def get_my_user_info(self):

		if self._username:
			return self.get_user_info(self.username)


class RedditUser(RedditAgent):

	def __init__(self,username,password):
		self.upvotees = {}
		self.downvotees = {}
		self.recent_scans = {}
		super(RedditUser,self).__init__(RedditSession(user=username,passwd=password))


	def __unicode__(self):
		return self._session._username

	def add_upvotee(self,username=None,userobj=None):
		self.upvotees[username]=None

	def add_downvotee(self,username=None,userobj=None):
		self.downvotees[username]=None


	def scan_user_for_unvoted_items(self,username=None,limit=5,posts=True,comments=True):

		if username in self.recent_scans:
			unvoted_comments,unvoted_posts = self.recent_scans[username]
			items = set()
			items.update(unvoted_posts)
			items.update(unvoted_comments)
			return items

		user_page = self.get_user_page(username)
		pages = []
		page_number =0
		while user_page and page_number < limit:
			pages.append(user_page)
			print "current page: %s" % (user_page)
			user_page = user_page.get_next_page()
			page_number = page_number +1
			print "page#: %s limit: %s" % (page_number,limit)
	
		unvoted_comments=[]
		unvoted_posts=[]
		for page in pages:
			for post in page.get_posts():
				if post.likes == None:
					unvoted_posts.append(post)
			for comment in page.get_comments():
				if comment.likes == None:
					unvoted_comments.append(comment)
		unvoted_comments = set(unvoted_comments)
		unvoted_posts = set(unvoted_posts)
		items = set()
		items.update(unvoted_posts)
		items.update(unvoted_comments)
		self.recent_scans[username]=(unvoted_comments,unvoted_posts)

		return  items
