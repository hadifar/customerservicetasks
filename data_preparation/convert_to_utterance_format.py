import argparse
import json
import operator
import os
import random
from itertools import chain

from sklearn.model_selection import train_test_split

from utils import clean_utterance_format
from utils import LANG_LIST
from utils import append_special_token
from utils import detect_utterance_langs
from utils import get_user_ids
from utils import remove_duplicate_user_ids


def convert_to_utterance(user_id, convs, all_replies, op, n_candidates=19):
    utterances = []

    # find operator replies pointers
    pointers = []
    for i, tweet in enumerate(convs):

        if i == 0:  # skip first tweet of conversation for pointers
            continue

        if op(tweet['author_id'].lower(), user_id):  # based on op() we add pointer,
            pointers.append(i)

    for i, p in enumerate(pointers):
        history = convs[:p]

        reply = convs[p]

        # randomly select 19 candidates + 1 ground truth reply
        flag = True
        candidates = []
        while flag:
            candidates = random.choices(all_replies, k=n_candidates)
            possible_ids = [item.get('tweet_id', None) for item in candidates]
            flag = reply['tweet_id'] in possible_ids or None in possible_ids

        candidates.append(reply)
        history = [h['text'] for h in history]
        candidates = [c['text'] for c in candidates]

        if (reply['tweet_lang'] == 'und') or (reply['tweet_lang'] not in LANG_LIST):
            c = detect_utterance_langs(reply['text'], history, candidates)
            if c == 'unk':
                continue
            else:
                reply['tweet_lang'] = c

        utterances.append({"candidates": candidates, "history": history, "lang": [reply['tweet_lang']]})

    return utterances


def create_utterance_format(user_id, conversations, n_candidates, utterance_type):
    all_operator_replies = []
    all_client_replies = []
    for convs in conversations:
        for tweet in convs:
            if tweet['author_id'].lower() == user_id:
                all_operator_replies.append(tweet)
            else:
                all_client_replies.append(tweet)

    # each conversation contains 1 or more utterances which may start by user or operator
    all_utterances = []
    for convs in conversations:
        if utterance_type == 'operator':
            tmp = convert_to_utterance(user_id, convs, all_operator_replies, operator.eq, n_candidates)
        elif utterance_type == 'client':
            tmp = convert_to_utterance(user_id, convs, all_client_replies, operator.ne, n_candidates)
        elif utterance_type == 'full':
            tmp1 = convert_to_utterance(user_id, convs, all_operator_replies, operator.eq, n_candidates)
            tmp2 = convert_to_utterance(user_id, convs, all_client_replies, operator.ne, n_candidates)
            tmp = tmp1 + tmp2
        else:
            raise Exception("specify utterance type ...")

        if len(tmp) != 0:
            all_utterances.append(tmp)

    # if utterance_type == 'operator':
    #     print("Operator replies", len(all_operator_replies))
    # elif utterance_type == 'client':
    #     print("Client replies", len(all_client_replies))
    # elif utterance_type == 'full':
    # print("Operator+Client replies", len(all_client_replies) + len(all_operator_replies))

    return all_utterances


def sort_conversations_by_time(conversations):
    # sort conversations based on first reply creation time
    conversations.sort(key=lambda x: x[0]['created_at'])
    return conversations


def add_special_to_conversations(conversations, user_id):
    for convs in conversations:
        for tweet in convs:
            tweet['text'] = append_special_token(tweet['text'], tweet['author_id'].lower() == user_id)
    return conversations


def save_to_disk(raw_conversations, file_path, mode, user_id=None, task=None):
    print(len(raw_conversations))
    file_name = "{}.json".format(mode) if user_id is None else "{}_{}_{}.json".format(mode, task, user_id)
    with open(os.path.join(file_path, file_name), 'w') as outfile:
        for item in raw_conversations:
            outfile.write(json.dumps(item))
            outfile.write('\n')


def do_steps(args, mode, user_ids):
    all_raw = []

    for user_id in user_ids:
        print('{}-->{}'.format(mode, user_id))
        clean_conversations = clean_utterance_format(user_id=user_id,
                                                     dir_path=args.dir_path,
                                                     clean_type=args.clean_type)

        # sort based on time
        clean_conversations = sort_conversations_by_time(clean_conversations)

        clean_conversations = create_utterance_format(user_id=user_id,
                                                      utterance_type=args.utterance_type,
                                                      conversations=clean_conversations,
                                                      n_candidates=5)

        print('-' * 50)
        print(len(clean_conversations))

        # flatten utterances
        all_raw.append(list(chain(*clean_conversations)))

    save_to_disk(list(chain(*all_raw)), args.dir_path, mode)


def main(args):
    user_ids = get_user_ids(args.user_id)
    user_ids = remove_duplicate_user_ids(user_ids)

    # train_companies, valid_companies = train_test_split(user_ids, test_size=0.05, random_state=42)

    print('training files...')
    do_steps(args, 'train', user_ids)
    # print('test files...')
    # do_steps(args, 'test', valid_companies)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument('--user_id', type=str, default='user_ids.txt',
                        help="user id(s) to retrieve its conversations e.g, OrangeBENL")
    parser.add_argument('--dir_path', type=str, default='./corpora-latest',
                        help="directory to save the conversations")

    parser.add_argument('--clean_type', type=str, default='medium', help='level of pre-processing:',
                        choices=['medium', 'hard', 'soft', 'none'])
    parser.add_argument('--utterance_type', type=str, default='full', help='include client replies',
                        choices=['full', 'client', 'operator'])

    main(parser.parse_args())
