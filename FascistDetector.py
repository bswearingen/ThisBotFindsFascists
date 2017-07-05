import os
import time
import praw
import re
import collections
import datetime
import string
import sys

from cryptography.fernet import Fernet

reddit = praw.Reddit(client_id=os.environ['REDDIT_ID'],
                     client_secret=os.environ['REDDIT_SECRET'],
                     password=os.environ['REDDIT_PASS'],
                     user_agent=os.environ['REDDIT_AGENT'],
                     username=os.environ['REDDIT_USER'])

secret_key=os.environ['SECRET_KEY']
f = Fernet(str.encode(secret_key))
users = [
b'gAAAAABZHiuBhK0XumuvX6WI4s_jXhHAEvQLHOKXiRmaK579hjjl52xOSmrhkUgzluJEPJz3v01x8ZCpW-9cGWJ0tHhBUwTe-Q==',
b'gAAAAABZHi72t-wHJaAs0od_StzsdjxtSPJedJs1Bvn261mRivadlcESs4Zbb5ockyy9JV2NJ492LPxshlOTmgeD-5jYZ-rm7w==',
b'gAAAAABZHi8M7ejE0mW91Ulh9N2OpNLjL_q0tOpZccZlVSQOqdFuFP5sn7QGByNi-fIp1-oSmZmo9fN-4nGIZ69kfowfJesOrVPKTptKo1WPR6kGlb5W0ZA='
]
slurs = [
'allah akbar',
'beaner', 'beaney', 'blackpill', 'black pill', 'btfo',
'chink', 'coontown', 'cuck', 'cucked', 'codeword for anti-white', 'codeword for white genocide', 'classical liberal', 'classical liberalism', 'chimp out',
'darky', 'darkey', 'darkie', 'degeneracy', 'degenerate', 'dindu', 'dindu nuffin',
'ethnic nationalist', 'ethno national', 'ethno-national',
'fag', 'faggot',
'gook', 'goy', 'goyim', 'goyum', 'groid', 'gyppo', 'gippo', 'gypo', 'gyppie', 'gyppy', 'gipp', 'gorillion', 'globalist', 'globalism', 'gib', 'gibsmedat',
'heeb', 'hebe', 'hymie',
'jew', 'jidf',
'kebab', 'kike', 'kyke', 'kangs', 'kangz',
'leftard', 'leftist', 'leftism', 'liberalism', 'libtard',
'multicultural', 'multiculturalism', 'multiculturalist', 'marxist', 'cultural marxism', 'mongrel',
'niglet', 'nig-nog', 'nignong', 'nigger', 'nigga', 'niggar', 'nip', 'negro',
'oy vey',
'pikey', 'piky', 'piker', 'peaceful ethnic cleansing', 'pikie',
'queer',
'rapefugee','race realist', 'redpill', 'red pill', 'race mix', 'radical islamic terror', 'religion of peace', 'regressive left',
'shylock', 'spearchucker', 'spick', 'shitskin', 'shill', 'shekel', 'shoah', 'soros', 'sjw', 'sharia', 'snackbar',
'the whites', 'the white race', 'the blacks', 'tranny', 'thug',
'virtue signal',
'wetback', 'wop', 'white nationalist', 'white genocide', 'we must secure the existence of our people and a future for white children',
'yid', 'youths', 'young male',
'1488'
]

#Add in standard plurals
with_plural_slurs = slurs + [slur + 's' for slur in slurs] + [slur + 'z' for slur in slurs]

multi_word_slurs = [slur for slur in with_plural_slurs if ' ' in slur]
single_word_slurs = [slur for slur in with_plural_slurs if ' ' not in slur]

# Our punctuation remover
translator = str.maketrans('', '', string.punctuation)

def CheckUser(redditorSuspect, recMessage):
	incidents = []
	lastCommentID = ''
	for comment in redditorSuspect.comments.new(limit=None):
		quoteFree = re.sub(r">.*\n", "", comment.body).strip('#\n \t')
		contained = []
		# Check against multi-word slurs, as they're unique enough to just do a string compare
		contained.extend([slur for slur in multi_word_slurs if slur in quoteFree.lower()])

		# Check against echo parentheses 
		if('(((' in quoteFree and ')))' in quoteFree):
			contained.extend(['(((',')))'])

		# Strip the punctuation, split the comment into single words, check against all our single word slurs
		contained.extend([slur for slur in single_word_slurs if slur in quoteFree.lower().translate(translator).split()])

		if contained:
			if lastCommentID == '':
				url = 'http://np.reddit.com/comments/' + comment.link_id[3:] + '/_/' + comment.id
			else:
				url = 'http://www.reddit.com/user/' + redditorSuspect.name + '/comments/?limit=1&after=t1_' + lastCommentID
			abstract = re.sub('\(http.*\)', '', quoteFree.split('\n')[0])
			incidents.append('\n* **/r/' + repr(comment.subreddit.display_name).rstrip('\'').lstrip('\'') + ' - ' + repr(contained) + '** - [' + abstract + '](' + url + ')')
			
		lastCommentID = comment.id

	messageBodies = ['']

	if not incidents:
		recMessage.reply('Nothing found: /u/' + redditorSuspect.name)
		return
		
	for incident in incidents:
		if len(messageBodies[-1]) + len(incident) < 10000:
			messageBodies[-1] += incident
		else:
			messageBodies.append(incident)

	for messageBody in reversed(messageBodies):
		recMessage.reply(messageBody)

while(True):
	messages = reddit.inbox.unread(mark_read=True);

	for rMessage in messages:
		rMessage.mark_read()
		if str.encode(rMessage.author) in [f.decrypt(user) for user in users] and rMessage.subject != 'comment reply':
			try:
				if rMessage.subject == 'username mention':
					parent = reddit.comment(rMessage).parent()
					CheckUser(parent.author, rMessage)
				else:
					CheckUser(reddit.redditor(re.sub('/.*?/','', rMessage.body)), rMessage)
			except:
				rMessage.reply('Error parsing: /u/' + re.sub('/.*?/','', rMessage.body))