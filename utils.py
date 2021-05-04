# -*- coding: utf-8 -*-
#
# Copyright 2020 Amir Hadifar. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import os
from collections import Counter
import re
import emoji
from nltk import TweetTokenizer
import json

from polyglot.detect import Detector

LANG_LIST = ['en', 'fr', 'nl', 'de']
AT_OPERATOR = '<at_operator>'
AT_CLIENT = '<at_client>'
AT_OTHERS = '<at_other>'
FROM_OPERATOR = '<from_operator>'
FROM_CLIENT = '<from_client>'

USER = '<at_user>'
URL = '<http_url>'
# OPERATOR_NAME = '<op_name>'

tknzr = TweetTokenizer(reduce_len=True)


def remove_duplicate_user_ids(all_user_ids):
    return list(Counter(all_user_ids).keys())


def get_user_ids(user_ids):
    if os.path.isfile(user_ids):
        with open(user_ids) as inpfile:
            lines = inpfile.readlines()
            return [user.lower().rstrip() for user in lines]

    elif isinstance(user_ids, list):
        return [item.lower() for item in user_ids]
    else:
        return user_ids.lower().split()


def find_match_double_wedge(str):
    res = re.search('\^\^(\w+)', str)
    if not res:
        return ''
    return res.group(1)


def find_match_single_wedge(str):
    res = re.search('\^(\w+)', str)
    if not res:
        return ''
    return res.group(1)


def is_proper_conversation(convs):
    # skip conversations with 1 turn
    if len(convs) < 2:
        return False
    if len(set([t['author_id'].lower() for t in convs])) == 1:  # ignore one participant conversations
        return False
    return True


def is_tweet_from_operator(user_id, tweet):
    return tweet['author_id'].lower() == user_id


def append_special_token(tweet, tweet_from_operator):
    # concat special tokens
    if len(tweet.split()) > 0:
        if tweet_from_operator:
            tweet = FROM_OPERATOR + ' ' + tweet
        else:
            tweet = FROM_CLIENT + ' ' + tweet

        # remove extra spaces
        tweet = " ".join(tweet.split())
        return tweet
    else:
        return None


def clean_utterance_format(user_id, dir_path, clean_type='medium'):
    dir_path = "{}/{}".format(dir_path, user_id)
    inp_file_name = "{}/dialogue-{}-clean.txt".format(dir_path, user_id)

    all_conversations = []
    with open(inp_file_name, 'r') as inpfile:
        for conversation in inpfile:
            convs = json.loads(conversation)

            if not is_proper_conversation(convs):  # check length and single participant conversation
                continue

            new_convs = []

            for tweet in convs:

                tweet_from_operator = is_tweet_from_operator(user_id, tweet)
                in_reply_to_screen_name = tweet['in_reply_to_screen_name']

                if clean_type == 'medium':
                    t = clean_tweet_medium(tweet['text'], tweet_from_operator)
                elif clean_type == 'hard':
                    t = clean_tweet_hard(tweet['text'], tweet_from_operator, user_id, in_reply_to_screen_name)
                elif clean_type == 'soft':
                    t = clean_tweet_soft(tweet['text'], tweet_from_operator)
                elif clean_type == 'none':
                    t = clean_tweet_none(tweet['text'], tweet_from_operator)
                else:
                    raise Exception("Specify clean type...")

                if t:
                    tweet['text'] = t
                    new_convs.append(tweet)

            if len(new_convs) > 1:
                all_conversations.append(new_convs)

    return all_conversations


def preprocess_emoji(tweet):
    return emoji.demojize(tweet, use_aliases=True)


def get_replies(dir_path, user_id):
    dir_path = "{}/{}".format(dir_path, user_id)
    inp_file_name = "{}/dialogue-{}-clean.txt".format(dir_path, user_id)

    operator_replies = []

    with open(inp_file_name, 'r') as inpfile:
        for conversation in inpfile:
            convs = json.loads(conversation)

            if not is_proper_conversation(convs):  # check length and single participant conversation
                continue

            for i, tweet in enumerate(convs):
                tweet_from_operator = is_tweet_from_operator(user_id, tweet)
                if i != 0 and tweet_from_operator:
                    tweet = clean_tweet_medium(tweet['text'], tweet_from_operator)
                    operator_replies.append(tweet)

    return operator_replies


def preprocess_lowering(tweet):
    tweet = str(tweet).lower()
    tweet = " ".join(tweet.split())
    return " ".join(tknzr.tokenize(tweet))


def clean_tweet_none(tweet, tweet_from_operator):
    tweet = preprocess_emoji(tweet)
    # tweet = append_special_token(tweet, tweet_from_operator)
    return tweet


def clean_tweet_soft(tweet, tweet_from_operator):
    tweet = preprocess_lowering(tweet)
    tweet = preprocess_emoji(tweet)
    return tweet


def clean_tweet_medium(tweet, tweet_from_operator=False):
    tweet = preprocess_lowering(tweet)
    tweet = preprocess_emoji(tweet)

    #################################################################
    # replace http with URL
    tweet = re.sub(r"http\S+", URL, tweet)
    while tweet.find(URL + ' ' + URL) != -1:
        tweet = tweet.replace(URL + ' ' + URL, URL)

    pat = re.compile(r'@([^\s:]+)')
    all_mentions = re.findall(pat, tweet)
    for mention in all_mentions:
        tweet = str(tweet).replace('@' + mention, USER)

    while tweet.find(USER + ' ' + USER) != -1:
        tweet = tweet.replace(USER + ' ' + USER, USER)

    return tweet


def clean_tweet_hard(tweet, tweet_from_operator=False, user_id=None, in_reply_to_screen_name=None):
    tweet = preprocess_lowering(tweet)
    tweet = preprocess_emoji(tweet)

    #################################################################
    # replace http with URL
    tweet = re.sub(r"http\S+", URL, tweet)
    while tweet.find(URL + ' ' + URL) != -1:
        tweet = tweet.replace(URL + ' ' + URL, URL)
    # if tweet_from_operator:
    #     s2 = find_match_double_wedge(tweet['text'])  # ^^ operator_name
    #     if s2 != '' and ((len(tweet['text']) - tweet['text'].find(s2)) < 10):
    #         tweet['text'] = tweet['text'].replace('^^' + s2, ' ^' + 'operator')
    #
    #     s1 = find_match_single_wedge(tweet['text'])  # ^ operator_name
    #     if s1 != '' and ((len(tweet['text']) - tweet['text'].find(s1)) < 10):
    #         tweet['text'] = tweet['text'].replace('^' + s1, ' ^' + 'operator')

    #######################################################
    # lower case all mentions
    pat = re.compile(r'@([^\s:]+)')
    # all_mentions = re.findall(pat, tweet['text'])
    # for mention in all_mentions:
    #     tweet['text'] = str(tweet['text']).replace(mention, mention.lower())

    # replace operator ids
    if user_id:
        tweet = tweet.replace("@" + user_id.lower(), AT_OPERATOR)
        tweet = tweet.replace(user_id.lower(), AT_OPERATOR)

    # replace user ids
    if tweet_from_operator and in_reply_to_screen_name:  # operator reply
        tweet = tweet.replace('@' + in_reply_to_screen_name.lower(), AT_CLIENT)
        tweet = tweet.replace(in_reply_to_screen_name.lower(), AT_CLIENT)

        # replace other mentions by <others>
        tweet = re.sub(pat, AT_OTHERS, tweet)

    # remove duplicate mentions e.g. <others><others> --> <others>
    while tweet.find(AT_OTHERS + ' ' + AT_OTHERS) != -1:
        tweet = tweet.replace(AT_OTHERS + ' ' + AT_OTHERS, AT_OTHERS)

    # at beginning of each tweet add special token
    if tweet_from_operator and tweet.startswith(AT_CLIENT):
        tweet = tweet.replace(AT_CLIENT, '', 1)

    elif not tweet_from_operator and tweet.startswith(AT_OPERATOR):
        tweet = tweet.replace(AT_OPERATOR, '', 1)

    #################################################################
    # tweet = append_special_token(tweet, tweet_from_operator)
    return tweet


def detect_utterance_langs(reply, history, candidates):
    try:
        c = Detector(reply, quiet=True).language.code
        if c in LANG_LIST:
            return c
        else:
            raise Exception()
    except:
        try:
            txt = " ".join(history) + " " + reply
            c = Detector(txt, quiet=True).language.code
            if c in LANG_LIST:
                return c
            else:
                raise Exception()
        except:
            try:
                txt = " ".join(history) + " " + reply + " " + ' '.join(candidates)
                c = Detector(txt, quiet=True).language.code
                if c in LANG_LIST:
                    return c
                else:
                    return 'unk'
            except:
                return 'unk'


def detect_langs(text):
    try:
        c = Detector(text, quiet=True).language.code
        if c in LANG_LIST:
            return c
    except:
        return "unk"
