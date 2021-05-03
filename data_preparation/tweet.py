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
import json


class TweetObject:
    def __init__(self, tweet=None):
        if tweet:
            self.tweet_id = tweet.id
            self.author_id = tweet.user.screen_name
            self.created_at = str(tweet.created_at)
            self.text = " ".join(tweet.full_text.split())
            self.in_response_to_id = tweet.in_reply_to_status_id
            self.in_reply_to_screen_name = tweet.in_reply_to_screen_name
            self.tweet_lang = tweet.lang

    def serialize(self):
        return json.dumps(self.__dict__)

    def set(self, tid, author_id, created_at, text, in_response_to_id, in_reply_to_screen_name, tweet_lang):
        self.tweet_id = tid
        self.author_id = author_id
        self.created_at = created_at
        self.text = text
        self.in_response_to_id = in_response_to_id
        self.in_reply_to_screen_name = in_reply_to_screen_name
        self.tweet_lang = tweet_lang
        return self

    def __eq__(self, o):
        return self.tweet_id == o.tweet_id and \
               self.author_id == o.author_id and \
               self.created_at == o.created_at and \
               self.text == o.text and \
               self.in_response_to_id == o.in_response_to_id and \
               self.in_reply_to_screen_name == o.in_reply_to_screen_name and \
               self.tweet_lang == o.tweet_lang


class ConversationObject:
    def __init__(self, list_of_tweets):
        self.tweets = list_of_tweets

    def serialize(self):
        return json.dumps([ob.__dict__ for ob in self.tweets])

    def __eq__(self, other):
        for t1, t2 in zip(self.tweets, other.tweets):
            if t1 != t2:
                return False
        return True

    def partially_equal(self, new_conversation):
        partial_equal = False
        if len(new_conversation.tweets) == len(self.tweets):
            return partial_equal  # return false since we alrady check this condition
        else:
            for t_new in new_conversation.tweets:
                for t_old in self.tweets:
                    if t_new == t_old:
                        partial_equal = True
                        break

        return partial_equal
