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
import argparse
import json
import math
import os

import tweepy

from config import get_config
from tweet import TweetObject, ConversationObject
from utils import get_user_ids
from utils import remove_duplicate_user_ids


def is_conversation_exist(src_tweet, all_conversation):
    for src, history in all_conversation:
        for h in history:
            if h.text == src_tweet.text:
                return True
    return False


def refine_user_conversation(c):
    src, hist = c[0], c[1]
    hist = list(reversed(hist))
    hist.append(src)
    return ConversationObject(hist)


def save_to_file(all_conversations, user_id, path):
    dir_path = "{}/{}".format(path, user_id)
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)

    file_name = "{}/dialogue-{}.txt".format(dir_path, user_id)
    with open(file_name, 'w') as outfile:
        for item in all_conversations:
            outfile.write(item.serialize())
            outfile.write('\n')


def crawl_conversations_for_user_id(user_id, api, max_page_to_crawl=math.inf):
    print('start crawling {} for max page of {}'.format(user_id, max_page_to_crawl))

    conversations = {}
    page = 1
    while True:
        statuses = api.user_timeline(page=page, id=user_id, tweet_mode="extended")
        if statuses:
            for tweet in statuses:

                src_tweet = TweetObject(tweet)

                history_tweets = []

                # get all replies to this tweet
                while tweet.in_reply_to_status_id:
                    try:
                        tweet = api.get_status(tweet.in_reply_to_status_id, tweet_mode="extended")
                        trg_tweet = TweetObject(tweet)
                        history_tweets.append(trg_tweet)
                    except:
                        print('tweet id {} not found!'.format(tweet.id))
                        break

                if len(history_tweets) == 0:
                    continue

                if conversations.get(src_tweet.in_reply_to_screen_name) is None:
                    conversations[src_tweet.in_reply_to_screen_name] = [[src_tweet, history_tweets]]

                else:
                    is_exist = is_conversation_exist(src_tweet, conversations[src_tweet.in_reply_to_screen_name])
                    if is_exist:  # we already crawl this conversation
                        continue
                    else:
                        conversations[src_tweet.in_reply_to_screen_name].append([src_tweet, history_tweets])
        else:
            break
        print('-' * 20, ' Page number: {} '.format(page), '-' * 20)
        page += 1  # next page

        if page > max_page_to_crawl:
            break

    # refine conversations
    conversations = compact_conversation(conversations)
    return conversations


def get_api(args):
    config = get_config(args.api_account)

    if config.API_KEY is None:
        raise Exception("use your own credential")

    auth = tweepy.OAuthHandler(config.API_KEY, config.API_SEC_KEY)
    auth.set_access_token(config.ACCESS_TOKEN, config.ACCESS_TOKEN_SEC)
    return tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, retry_delay=5, retry_count=1)


def convs_file_exists(user_id, dir_path):
    dir_path = "{}/{}".format(dir_path, user_id)
    file_path = dir_path + '/dialogue-' + user_id + '.txt'
    return os.path.exists(file_path)


def merge_conversations(new_conversations, old_conversations):
    # change list of tweets to convs format
    total_conversations = old_conversations.copy()

    # helper function to check whether convs already exist or not
    def conv_already_exist(new_conv, all_old_convs):
        # check exact conversation exist
        for i, old_conv in enumerate(all_old_convs):
            if len(new_conv.tweets) == len(old_conv.tweets) and new_conv == old_conv:
                return -1  # exact same conversations

        for i, old_conv in enumerate(all_old_convs):
            if old_conv.partially_equal(new_conv):
                return i  # already exist

        return -2  # totally new conversation

    n_update_convs = 0
    for new_conv in new_conversations:
        ind = conv_already_exist(new_conv, old_conversations)
        if ind == -1:  # exact conversation exist
            continue
        elif ind == -2:  # totally new conversation
            total_conversations.append(new_conv)
        else:  # convs partially exists
            n_update_convs += 1
            total_conversations.pop(ind)
            total_conversations.append(new_conv)

    print(len(total_conversations) - len(old_conversations), 'new conversation found')
    print(n_update_convs, 'conversations updated..')
    return total_conversations


def compact_conversation(crawled_conversations):
    new_converation = []
    for item in crawled_conversations.items():
        usr, all_user_conversations = item
        for c in all_user_conversations:
            new_converation.append(refine_user_conversation(c))

    return new_converation


def update_conversation_for_user_id(user_id, dir_path, api):
    dir_path = "{}/{}".format(dir_path, user_id)
    inp_file_name = dir_path + '/dialogue-' + user_id + '.txt'

    new_conversation = crawl_conversations_for_user_id(user_id, api, max_page_to_crawl=50)  # crawl 50 pages

    old_conversations = []
    with open(inp_file_name, 'r') as inpfile:
        for conversation in inpfile:
            convs = json.loads(conversation)
            convs = [TweetObject().set(item['tweet_id'],
                                       item['author_id'],
                                       item['created_at'],
                                       item['text'],
                                       item['in_response_to_id'],
                                       item['in_reply_to_screen_name'],
                                       item['tweet_lang']) for item in convs]
            convs = ConversationObject(convs)
            old_conversations.append(convs)

    return merge_conversations(new_conversation, old_conversations)


def main(args):
    """
    if conversations for a user already crawled we only retrieve last 50 pages (update_conversation_for_user_id)
    otherwise we crawl conversations as much as possible (crawl_conversations_for_user_id).
    """
    # list of users to crawl
    user_ids = get_user_ids(args.user_id)
    user_ids = remove_duplicate_user_ids(user_ids)

    # setup credential for twitter api
    api = get_api(args)

    # loop through every user to crawl its churn_data
    for user_id in user_ids:
        print('-' * 50)
        print(user_id)
        print('-' * 50)
        if convs_file_exists(user_id, args.dir_path):
            all_convs = update_conversation_for_user_id(user_id, args.dir_path, api)
        else:
            all_convs = crawl_conversations_for_user_id(user_id, api,
                                                        max_page_to_crawl=args.max_page_to_crawl)  # list(tweetObject)

        save_to_file(all_convs, user_id, args.dir_path)


if __name__ == '__main__':
    # This file only crawl data
    # You should call preproces.py in order to clean data
    # For final conversation format call convert_to_utterance_format.py

    parser = argparse.ArgumentParser()
    parser.add_argument('--user_id', type=str, default='companies_twitter_ids_test.txt',
                        help="user id(s) to retrieve its conversations e.g, OrangeBENL")
    parser.add_argument('--dir_path', type=str, default='./corpora-latest',
                        help="directory to save the conversations")

    parser.add_argument('--max_page_to_crawl', type=int, default=math.inf,
                        help="directory to save the conversations")

    parser.add_argument('--api_account', type=str, default='myself',
                        help="default api account to download tweets. See config.py")

    args = parser.parse_args()

    main(args)
