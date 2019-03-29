import numpy as np
import pandas as pd
import re
import os
import requests
import matplotlib.pyplot as plt

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

from gensim.scripts.glove2word2vec import glove2word2vec
from gensim.models.keyedvectors import KeyedVectors

from sklearn.linear_model import LogisticRegression
from sklearn import svm

print('Model is being trained...Please wait')
# If glove embeds is not in word2vec form then first convert it then load it
if os.path.isfile('pretrained_embeds/gensim_glove_vectors.txt'):
    glove_model = KeyedVectors.load_word2vec_format("pretrained_embeds/gensim_glove_vectors.txt", binary=False)
else:
    glove2word2vec(glove_input_file="pretrained_embeds/glove.twitter.27B.25d.txt", word2vec_output_file="pretrained_embeds/gensim_glove_vectors.txt")
    glove_model = KeyedVectors.load_word2vec_format("pretrained_embeds/gensim_glove_vectors.txt", binary=False)

def get_embed(word):
    # Case folding
    word = word.lower()
    try:
        return (glove_model.get_vector(word))
    except:
        return (glove_model.get_vector('unk'))


data = pd.read_csv('data.csv')

total = 0
ones = 0

data_embeds = []
label = []

stop_words = set(stopwords.words('english'))

for index, row in data.iterrows():

    sent = row['text_message']
    sent = sent.replace('\n','')                                # Remove new lines
    sent = sent.replace('\t',' ')                               # Remove tabs
    sent = re.sub(r'http\S+', '', sent, flags=re.MULTILINE)     # Remove urls
    sent = re.sub(r'[^\w\s]','', row['text_message'])           # Remove punctuations
    sent = sent.lower().strip()                                 # Case folding
    sent = word_tokenize(sent)                                  # Tokenization
#     sent = [i for i in sent if i not in stop_words]
    
    temp = [get_embed(i) for i in sent]
    temp = np.array(temp)
    temp = temp.mean(axis=0)
    data_embeds.append(temp)
    label.append(row['label_bullying'])

# Train-Test split
partition = int(0.8*len(data))
train = data_embeds[:partition]
train_y = label[:partition]

test = data_embeds[partition:]
test_y = label[partition:]

clf = svm.SVC(C=10, gamma='scale')
clf.fit(train, train_y)
print('Training Done, Test accuracy: ' + str(clf.score(test, test_y)))



def get_prediction(representation):
	return clf.predict(representation)

def get_prediction_prob(representation):
	return clf.decision_function(representation)