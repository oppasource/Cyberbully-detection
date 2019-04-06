import json
import os
import pdb
import numpy as np
import pandas as pd

from nltk.tokenize import TweetTokenizer

import get_comments as gc
import classifier as cl
from util.settings import Settings


tknzr = TweetTokenizer(strip_handles=True, reduce_len=True, preserve_case= False)



def preprocess_comment(comment):
    comment = tknzr.tokenize(comment)
    comment = [w for w in comment if w.encode("ascii", errors="ignore").decode() == w]
    return comment

def create_representation(processed_comment):
	temp = [cl.get_embed(i) for i in processed_comment]
	temp = np.array(temp)
	temp = temp.mean(axis=0)
	return temp

def predict(comment):
	representation = np.array([create_representation(comment)])
	classification = cl.get_prediction(representation)
	prob = cl.get_prediction_prob(representation)
	return prob[0], classification[0]


####### Getting input  ######
def get_stats(usrname):
	if os.path.exists("profiles/" + usrname + ".json"):
		jdata = json.load(open("profiles/" + usrname + ".json", 'r'))
	else:	
		info_dump = gc.get_info(usrname)
		jdata = info_dump



	dp_link = jdata['prof_img']
	post_n_comments = {}
	df = pd.DataFrame(columns=['post_url', 'commented_by', 'comment', 'bully_or_not', 'confidence_score'])


	for post in jdata['posts']:
		post_url = post['url']
		post_n_comments[post_url] = {}

		for comment in post['comments']['list']:
			# Ignore captions and self comments
			if comment['user'] != usrname:
				processed_comment = preprocess_comment(comment['comment'])
				# Only if textual conent is there in the processed comment
				if processed_comment:
					confidence_score, classification = predict(processed_comment)
					post_n_comments[post_url][comment['user']] = [comment['comment'], classification, confidence_score]

					# Append row in dataframe
					df = df.append({'post_url': post_url, 'commented_by': comment['user'], 'comment': comment['comment'], 'bully_or_not': (classification), 'confidence_score': confidence_score}, ignore_index=True)


	# Calculating stats
	global_bully_percent = df['bully_or_not'].sum() / df['bully_or_not'].count()

	# Most bullied post
	df['bully_or_not'] = pd.to_numeric(df['bully_or_not'])
	temp_df = df.groupby(['post_url'], as_index=False).mean()
	most_bullied_post = temp_df[temp_df['bully_or_not'] == temp_df['bully_or_not'].max()]['post_url'].to_string().split()[-1]

	temp_df = temp_df[temp_df.post_url != most_bullied_post]
	second_most_bullied_post = temp_df[temp_df['bully_or_not'] == temp_df['bully_or_not'].max()]['post_url'].to_string().split()[-1]

	try:
		most_confident_bully = df[df['confidence_score'] == df['confidence_score'].max()].iloc[0]['post_url']
		if most_bullied_post != most_confident_bully:
			second_most_bullied_post = most_confident_bully
	except:
		pass

	
	bullied_comments_1st = df[df['post_url'] == most_bullied_post].sort_values(by = ['confidence_score'], ascending  = False)[['commented_by', 'comment']].iloc[:Settings.top_k_comments]
	bullied_comments_2nd = df[df['post_url'] == second_most_bullied_post].sort_values(by = ['confidence_score'], ascending  = False)[['commented_by', 'comment']].iloc[:Settings.top_k_comments]
	bullied_comments_1st = bullied_comments_1st.to_dict(orient='list')
	bullied_comments_2nd = bullied_comments_2nd.to_dict(orient='list')


	return_dict = {'dp_link': dp_link, 
					'bullied_percent': global_bully_percent, 
					'1st_post': {'link': most_bullied_post, 'comments': bullied_comments_1st},
					'2nd_post': {'link': second_most_bullied_post, 'comments': bullied_comments_2nd}}

	return return_dict
