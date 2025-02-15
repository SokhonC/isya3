# -*- coding: utf-8 -*-
"""test_project.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1hcNEOXvu2h7k5UKDObyn9zaCmd3DzKw6
"""

from io import BytesIO
import pickle
import pandas as pd
import re
from tensorflow import keras
from lxml import etree
from flask import Flask, request, jsonify, render_template
import nltk
from nltk import word_tokenize
import re, string, unicodedata
# import contractions
import inflect
from nltk.corpus import stopwords
from nltk.stem import LancasterStemmer, WordNetLemmatizer

with open('vectorizer1.pkl', 'rb') as file:
    loaded_vectorizer = pickle.load(file)

nn_model = keras.models.load_model("my_model1.keras")

rexp = re.compile('(<review>(.*?)</review>)', re.S)
mdsd_paths = [
    "./content/books/positive.review", "./content/books/negative.review", "./content/books/book.unlabeled",
    "./content/dvd/positive.review", "./content/dvd/negative.review", "./content/dvd/unlabeled.review",
    "./content/electronics/positive.review", "./content/electronics/negative.review", "./content/electronics/unlabeled.review",
    "./content/home/positive.review", "./content/home/negative.review", "./content/home/unlabeled.review",
              ]

# from google.colab import drive
# drive.mount('/content/drive')

data = []
targets = []
for mdsd_path in mdsd_paths:
    print('Processing', mdsd_path, '... ', end='', flush=True)

    with open(mdsd_path, mode='rt', encoding='utf-8', newline='\n') as f:
        xml_docs = f.read()

        for m in rexp.finditer(xml_docs):
            g = m.groups()[0]
            ff = BytesIO(g.encode('utf-8'))
            context = etree.iterparse(ff, recover=True)
            mdsd_data = {}
            for _, elem in context:
                cnt = elem.text
                if cnt is not None:
                    cnt = cnt.replace('\n', '')
                else:
                    cnt = ''
                mdsd_data[elem.tag] = cnt
            try:
                mdsd_review_text = mdsd_data['review_text']
                rating = mdsd_data['rating']
                data.append(mdsd_review_text)
                targets.append(rating)
            except KeyError:
                print(f'Some review do not contain text or labels')

    print('done')

df = pd.DataFrame(data={"rating": targets, "review": data})


nltk.download('punkt')

tokens = [word_tokenize(sen) for sen in df.review]



def remove_non_ascii(words):
    """Remove non-ASCII characters from list of tokenized words"""
    new_words = []
    for word in words:
        new_word = unicodedata.normalize('NFKD', word).encode('ascii', 'ignore').decode('utf-8', 'ignore')
        new_words.append(new_word)
    return new_words


def to_lowercase(words):
    """Convert all characters to lowercase from list of tokenized words"""
    new_words = []
    for word in words:
        new_word = word.lower()
        new_words.append(new_word)
    return new_words

#remove all punctuation
def remove_punctuation(words):
    """Remove punctuation from list of tokenized words"""
    new_words = []
    for word in words:
        new_word = re.sub(r'[^\w\s]', '', word)
        if new_word != '':
            new_words.append(new_word)
    return new_words

def replace_numbers(words):
    """Replace all interger occurrences in list of tokenized words with textual representation"""
    p = inflect.engine()
    new_words = []
    for word in words:
        if word.isdigit():
            new_word = p.number_to_words(word)
            new_words.append(new_word)
        else:
            new_words.append(word)
    return new_words


def normalize(words):
    words = remove_non_ascii(words)
    words = to_lowercase(words)
    words = remove_punctuation(words)
    words = replace_numbers(words)
    return words



def lemmatize_verbs(words):
    """Lemmatize verbs in list of tokenized words"""
    lemmatizer = WordNetLemmatizer()
    lemmas = []
    for word in words:
        lemma = lemmatizer.lemmatize(word, pos='v')
        lemmas.append(lemma)
    return lemmas

nltk.download('wordnet')
# df['tokens'] = df['tokens'].apply(lambda x: lemmatize_verbs(x))

# input text
test_review = """I have bought and returned three of these units now.
Each one has been defective, and finally I just gave up on returning the system.
The DVD player constantly gives "Bad Disc" errors and skips if there is even the slightest
smudge on a disc. The sound quality is very nice for the price, but since the player doesn't work,
it's essentially useless. This is a complete rip-off at any price point"""

def analyzeText(text):
    test_review = text
    # create dataframe
    test_df = pd.DataFrame({'review': [test_review]})

    # tokenize
    test_tokens = [word_tokenize(sen) for sen in test_df.review]
    # print(test_tokens)

    # remove stopwords
    # test_df['raw_tokens'] = [removeStopWords(sen) for sen in test_tokens]
    test_df['raw_tokens'] = test_tokens

    # normalize
    test_df['tokens'] = test_df['raw_tokens'].apply(lambda x: normalize(x))
    test_df['tokens'] = test_df['tokens'].apply(lambda x: lemmatize_verbs(x))
    test_sentence = test_df['tokens'].str.join(' ') ## join values into string
    print(test_sentence)
    X = loaded_vectorizer.transform(test_sentence)
    print("vectorized", X.shape)
    prediction = nn_model.predict(X)
    ratings = prediction[0]
    print(ratings)

    # Calculate negative and positive percentages
    negative_percentage = (ratings[0] + ratings[1]) * 100
    positive_percentage = (ratings[2] + ratings[3]) * 100

    # Print the results
    print(f"Negative: {negative_percentage:.2f}%")
    print(f"Positive: {positive_percentage:.2f}%")
    return [negative_percentage, positive_percentage]

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('./index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if request.method == 'POST':
        user_input = request.form['text']
        
        # Preprocess the input
        results = analyzeText(user_input)
        
        
        # Assuming the model outputs probabilities for two classes: [Negative, Positive]
        negative_percentage = round(results[0])
        positive_percentage = round(results[1])
        
        return render_template('result.html', 
                               text=user_input, 
                               negative=negative_percentage, 
                               positive=positive_percentage)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)