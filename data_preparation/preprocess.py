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
import datetime
import json
import re
import time
from collections import Counter
from operator import itemgetter

import pandas as pd
from nltk.tokenize import TweetTokenizer
from tabulate import tabulate

from utils import get_user_ids, detect_langs, is_proper_conversation
from utils import remove_duplicate_user_ids


def get_userids(args):
    user_ids = get_user_ids(args.user_id)
    user_ids = remove_duplicate_user_ids(user_ids)
    return user_ids


def readable_format_userid(user_id, dir_path):
    dir_path = "{}/{}".format(dir_path, user_id)
    inp_file_name = "{}/dialogue-{}-clean.txt".format(dir_path, user_id)
    out_file_name = "{}/dialogue-{}-readable.txt".format(dir_path, user_id)

    all_data = []
    with open(inp_file_name, 'r') as inpfile, open(out_file_name, 'w') as outfile:
        for conversation in inpfile:
            convs = json.loads(conversation)

            if is_proper_conversation(convs):
                convs_list = ['@' + tweet['author_id'] + ':: ' + tweet['text'] for tweet in convs]

            for tweet in convs:
                tmp = tweet['author_id'] + ': ' + tweet['text']
                outfile.write(tmp)
                outfile.write('\n')
            outfile.write('-' * 75 + '\n')
            if 6 > len(convs_list) > 0:
                convs_list = "\n".join(convs_list)
                all_data.append(convs_list)

    df = pd.DataFrame({'cid': [i for i in range(len(all_data))], 'conversation': all_data})
    df.to_csv(user_id + '_data.csv', index=False)


# def readable_format_userid(user_id, dir_path):
# dir_path = "{}/{}".format(dir_path, user_id)
# inp_file_name = "{}/dialogue-{}-clean.txt".format(dir_path, user_id)
# out_file_name = "{}/dialogue-{}-readable.txt".format(dir_path, user_id)
#
# all_data = []
# with open(inp_file_name, 'r') as inpfile, open(out_file_name, 'w') as outfile:
#     for conversation in inpfile:
#         convs = json.loads(conversation)
#         convs_list = [tweet['author_id'] + ': ' + tweet['text'] for tweet in convs]
#         for tweet in convs:
#             tmp = tweet['author_id'] + ': ' + tweet['text']
#             outfile.write(tmp)
#             outfile.write('\n')
#         outfile.write('-' * 75 + '\n')
#         all_data.append(convs_list)
# print(all_data)


def generate_stats_userid(user_id, dir_path):
    dir_path = "{}/{}".format(dir_path, user_id)
    inp_file_name = "{}/dialogue-{}-clean.txt".format(dir_path, user_id)
    out_file_name = "{}/dialogue-{}-stats.txt".format(dir_path, user_id)

    total_convs = 0
    total_tweets = 0
    total_tokens = 0
    avg_convs_turn = 0

    oldest_tweet_time = 10e20
    languages = {}
    conversation_length = {}
    total_operator_responses = 0
    total_users_responses = 0

    tknzr = TweetTokenizer(reduce_len=True)

    with open(inp_file_name, 'r') as inpfile:
        for conversation in inpfile:
            convs = json.loads(conversation)

            total_convs += 1
            avg_convs_turn += len(convs)

            # conversation distribution
            if conversation_length.get(len(convs)) is None:
                conversation_length[len(convs)] = 1
            else:
                conversation_length[len(convs)] += 1

            for tweet in convs:

                creation_date = datetime.datetime.strptime(tweet['created_at'], '%Y-%m-%d %H:%M:%S')
                millis = time.mktime(creation_date.timetuple()) * 1000

                if millis < oldest_tweet_time:
                    oldest_tweet_time = millis

                if tweet['author_id'].lower() == user_id.lower():
                    total_operator_responses += 1
                else:
                    total_users_responses += 1

                total_tweets += 1
                tmp = str(tweet['text'])
                tmp = tknzr.tokenize(tmp)
                total_tokens += len(tmp)

                if tweet.get('tweet_lang') and tweet.get('tweet_lang') in languages.keys():
                    languages[tweet['tweet_lang']] += 1
                else:
                    languages[tweet.get('tweet_lang', 'und')] = languages.get(tweet.get('tweet_lang', 'und'), 0) + 1

        avg_convs_turn = avg_convs_turn / total_convs
        avg_tweets_len = total_tokens / total_tweets
        avg_convs_tokens = total_tokens / total_convs

    # sort lang
    languages = sorted(languages.items(), key=itemgetter(1), reverse=True)
    # sort convs frequency:
    conversation_length = sorted(conversation_length.items(), key=itemgetter(1), reverse=True)

    table = [["Total # conversations", total_convs],
             ["Total # tweets", total_tweets],
             ["Total # tokens", total_tokens],
             ["AVG conversation turns", avg_convs_turn],
             ["AVG conversation tokens", avg_convs_tokens],
             ["AVG tweets length", avg_tweets_len],
             ["Languages", languages[0:4]],
             ["Total # of operator responses", total_operator_responses],
             ["Total # of users responses", total_users_responses],
             ["Conversation length stats", conversation_length],
             ["Oldest tweet extracted", datetime.datetime.fromtimestamp(oldest_tweet_time / 1000.0)],
             ]

    print(tabulate(table, tablefmt="fancy_grid"))

    with open(out_file_name, 'w') as outfile:
        outfile.write(tabulate(table, tablefmt="fancy_grid"))


# def topic_model_userid(user_id, dir_path, n_topics=10):
#     dir_path = "{}/{}".format(dir_path, user_id)
#     inp_file_name = "{}/dialogue-{}-clean.txt".format(dir_path, user_id)
#     out_file_name = "{}/dialogue-{}-topics-{}.txt".format(dir_path, user_id, n_topics)
#     out_file_name2 = "{}/dialogue-{}-topic-terms.txt".format(dir_path, user_id)
#
#     datasets = []
#
#     import string
#     stop_words = set(stopwords.words('english'))
#     punctuations = string.punctuation. \
#         replace('#', ''). \
#         replace('_', ''). \
#         replace('<', ''). \
#         replace('>', ''). \
#         replace('@', ''). \
#         replace(':', '')
#
#     with open(inp_file_name, 'r') as inpfile:
#         for conversation in inpfile:
#             convs = json.loads(conversation)
#             for tweet in convs:
#                 if tweet['author_id'].lower() == user_id.lower():
#                     text = str(tweet['text']).translate(str.maketrans('', '', punctuations))
#                     tokens = clean_tweet_medium(text).split()
#                     tokens = [w for w in tokens if not w in stop_words]
#                     datasets.append(tokens)
#
#     common_dictionary = Dictionary(datasets)
#     common_corpus = [common_dictionary.doc2bow(text) for text in datasets]
#     lda = LdaModel(common_corpus, num_topics=n_topics)
#
#     data_topics = []
#     for text in datasets:
#         topic = lda.get_document_topics(common_dictionary.doc2bow(text))[0][0]
#         tmp = [topic, " ".join(text)]
#         data_topics.append(tmp)
#
#     data_topics.sort(key=lambda x: x[0])
#
#     headers = ["Topic #", "Operator tweet"]
#
#     with open(out_file_name, 'w') as outfile:
#         outfile.write(tabulate(data_topics, headers, tablefmt="fancy_grid"))
#
#     topic_terms = []
#     for i in range(n_topics):
#         tmp = [common_dictionary[token_id] for token_id, prob in lda.get_topic_terms(i, 15)]
#         topic_terms.append([i, tmp])
#
#     with open(out_file_name2, 'w') as outfile:
#         outfile.write(tabulate(topic_terms, ['Topic', 'Terms'], tablefmt="fancy_grid"))


def clean_userid(user_id, dir_path, conv_len=2):
    dir_path = "{}/{}".format(dir_path, user_id)
    inp_file_name = "{}/dialogue-{}.txt".format(dir_path, user_id)
    out_file_name = "{}/dialogue-{}-clean.txt".format(dir_path, user_id)

    with open(inp_file_name, 'r') as inpfile, open(out_file_name, 'w') as outfile:
        for conversation in inpfile:
            convs = json.loads(conversation)
            if len(convs) < conv_len:
                continue
            else:
                outfile.write(conversation)


def clean_corpus(args):
    user_ids = get_userids(args)
    for user_id in user_ids:
        clean_userid(user_id, args.dir_path)


# def readable_corpus(args):
#     user_ids = get_userids(args)
#     for user_id in user_ids:
#         readable_format_userid(user_id, args.dir_path)


# def topic_model_corpus(args):
#     user_ids = get_userids(args)
#     for user_id in user_ids:
#         topic_model_userid(user_id, args.dir_path)


def generate_stats_corpus(args):
    user_ids = get_userids(args)
    for user_id in user_ids:
        generate_stats_userid(user_id, args.dir_path)


def generate_total_report(args):
    user_ids = get_userids(args)

    total_conversations = 0
    total_tweets = 0
    total_tokens = 0
    total_tweets_per_lang = {}
    total_length_convs = {}
    total_accounts = 0
    total_operator_responses = 0
    total_user_responses = 0
    tweets_per_domain = {'airline': 0, 'telecom': 0, 'public_transport': 0}
    convs_per_domain = {'airline': 0, 'telecom': 0, 'public_transport': 0}

    for user_id in user_ids:
        total_accounts += 1
        dir_path = "{}/{}".format(args.dir_path, user_id)
        inp_file_name = "{}/dialogue-{}-stats.txt".format(dir_path, user_id)
        domain = get_domain(user_id)

        with open(inp_file_name, 'r') as inpfile:

            for i, line in enumerate(inpfile.readlines()):
                if i == 1:
                    total_conversations += int(line.split()[-2])
                    convs_per_domain[domain] = convs_per_domain[domain] + int(line.split()[-2])
                elif i == 3:
                    total_tweets += int(line.split()[-2])
                    tweets_per_domain[domain] = tweets_per_domain[domain] + int(line.split()[-2])
                elif i == 5:
                    total_tokens += int(line.split()[-2])
                elif i == 13:  # language
                    langs = re.findall("\([^()]*\)", line[line.find('[') + 1:line.find(']')].replace('\'', ''))
                    langs = [l.replace('(', '').replace(')', '').split(', ') for l in langs]
                    langs = [(l[0], int(l[1])) for l in langs]
                    langs = dict(langs)
                    for lang_code, count in langs.items():
                        if lang_code in total_tweets_per_lang.keys():
                            total_tweets_per_lang[lang_code] += count
                        else:
                            total_tweets_per_lang[lang_code] = count

                elif i == 15:  # total number of operator responses
                    total_operator_responses += int(line.split()[-2])

                elif i == 17:  # total number of user responses
                    total_user_responses += int(line.split()[-2])

                elif i == 19:
                    convs_length = re.findall("\([^()]*\)", line[line.find('[') + 1:line.find(']')].replace('\'', ''))
                    convs_length = [l.replace('(', '').replace(')', '').split(', ') for l in convs_length]
                    convs_length = [(l[0], int(l[1])) for l in convs_length]
                    convs_length = dict(convs_length)
                    for c_length, count in convs_length.items():
                        if c_length in total_length_convs.keys():
                            total_length_convs[c_length] += count
                        else:
                            total_length_convs[c_length] = count

    out_file_name = "{}/total-reports.txt".format(args.dir_path)
    table = [["Total # conversations", total_conversations],
             ["Total # tweets", total_tweets],
             ["Total # tokens", total_tokens],
             ["Total # crawled account", total_accounts],
             ["Languages", list(total_tweets_per_lang.items())],
             ["Conversation Length", list(total_length_convs.items())],
             ['Total # user responses', total_user_responses],
             ['Total # operator responses', total_operator_responses],
             ['Tweets per domain', list(tweets_per_domain.items())],
             ['Conversation per domain', list(convs_per_domain.items())],
             ]

    with open(out_file_name, 'w') as outfile:
        outfile.write(tabulate(table, tablefmt="fancy_grid"))


def per_langs_stats(args):
    user_ids = get_user_ids(args.user_id)
    user_ids = remove_duplicate_user_ids(user_ids)

    langs_convs = {}
    langs_tweets = {}
    langs_turns = {}

    for user_id in user_ids:
        dir_path = "{}/{}".format(args.dir_path, user_id)
        inp_file_name = "{}/dialogue-{}-clean.txt".format(dir_path, user_id)

        # find operator replies pointers
        with open(inp_file_name, 'r') as inpfile:
            for conversation in inpfile:
                convs = json.loads(conversation)

                all_langs_in_cur_convs = []

                prev_turn_author = None

                for tweet in convs:
                    l = tweet['tweet_lang']
                    all_langs_in_cur_convs.append(l)
                    if langs_tweets.get(l) is None:
                        langs_tweets[l] = 1
                    else:
                        langs_tweets[l] += 1  # history + 1 candidate

                    if prev_turn_author != tweet['author_id'].lower():
                        prev_turn_author = tweet['author_id'].lower()
                        langs_turns[tweet.get('tweet_lang', 'und')] = langs_turns.get(tweet.get('tweet_lang', 'und'),
                                                                                      0) + 1

                if len(set(all_langs_in_cur_convs)) == 1:
                    if langs_convs.get(all_langs_in_cur_convs[0]) is None:
                        langs_convs[all_langs_in_cur_convs[0]] = 1
                    else:
                        langs_convs[all_langs_in_cur_convs[0]] += 1
                else:
                    most_common_lang = Counter(all_langs_in_cur_convs).most_common(1)[0]
                    if most_common_lang[1] > int(len(all_langs_in_cur_convs) / 2):
                        l = most_common_lang[0]
                    else:
                        l = detect_langs([t['text'] for t in convs])

                    if langs_convs.get(l) is None:
                        langs_convs[l] = 1
                    else:
                        langs_convs[l] += 1

    out_file_name = "{}/total-report-per-langs.txt".format(args.dir_path)

    langs_convs = sorted(langs_convs.items(), key=itemgetter(1), reverse=True)
    langs_tweets = sorted(langs_tweets.items(), key=itemgetter(1), reverse=True)
    langs_turns = sorted(langs_turns.items(), key=itemgetter(1), reverse=True)

    total_convs = sum([item[1] for item in langs_convs])
    total_tweets = sum([item[1] for item in langs_tweets])
    total_turns = sum([item[1] for item in langs_turns])

    table = [["conversation per lang", langs_convs],
             ["tweet per lang", langs_tweets],
             ['turn per lang', langs_turns],
             ["total conversation", total_convs],
             ["total tweets", total_tweets],
             ["total turns", total_turns],
             ]

    with open(out_file_name, 'w') as outfile:
        outfile.write(tabulate(table, tablefmt="fancy_grid"))


def get_domain(user_id):
    with open('data_preparation/companies_twitter_ids_airline_industry.txt') as inp_file:
        airline_company = inp_file.readlines()
        airline_company = [item.lower().replace('\n', '') for item in airline_company]
        if user_id.lower() in airline_company:
            return 'airline'

    with open('data_preparation/companies_twitter_ids_public_transport.txt') as inp_file:
        public_transport_company = inp_file.readlines()
        public_transport_company = [item.lower().replace('\n', '') for item in public_transport_company]
        if user_id.lower() in public_transport_company:
            return 'public_transport'

    with open('data_preparation/companies_twitter_ids_telecom.txt') as inp_file:
        telecom_company = inp_file.readlines()
        telecom_company = [item.lower().replace('\n', '') for item in telecom_company]
        if user_id.lower() in telecom_company:
            return 'telecom'


def main(args):
    clean_corpus(args)  # clean corpus (only truncated length) the main clean is done in utterance_format.py
    # readable_corpus(args)  # create readable format of the corpus
    generate_stats_corpus(args)  # generate some stats for each user_ids
    generate_total_report(args)  # stats based on all user_ids
    per_langs_stats(args)  # stats per language


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user_id', type=str, default='user_ids_french_rails.txt',
                        help="user id(s) to retrieve its conversations e.g, OrangeBENL")
    parser.add_argument('--dir_path', type=str, default='./corpora-latest',
                        help="directory to save the conversations")

    args = parser.parse_args()
    main(args)
