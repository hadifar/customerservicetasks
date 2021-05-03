# Data Preparation instruction

This folder provides a script to crawl and preprocess Twitter conversations. The sample output for each step can be found in corpora folder.

## Crawl 
To crawl Twitter conversations for a particular user(s) run the following script:

` python data_preparation/crawl_conversations.py --user_id data_preparation/companies_twitter_ids_test.txt --dir_path data_preparation/corpora/ --max_page_to_crawl 2 --api_account 'myself'`

- `user_id` is a text-file (see `companies_twitter_ids.txt`) or list of usernames which we aim to crawl
- `dir_path` is a directory to save the crawled conversations
- `max_page_to_crawl` is the number of pages to crawl per twitter account (default value is inf because we want to download all pages)
- `api_account` is a configuration file that is required to access twitter API (see `config.py`)

If you run the above script multiple times, it only adds/updates new conversations to existing ones. The above script creates a folder per twitter account and stores necessary metadata alongside with each conversation. 

## Preprocess 

The preprocessing step includes multiple steps such as truncate by conversation length, generate some statistics, etc.
To execute preprocessing step run the following command:

``python data_preparation/preprocess.py --user_id data_preparation/companies_twitter_ids_test.txt --dir_path data_preparation/corpora/``


## Utterance format

We perform another round of preprocessing and cleaning to obtain suitable format for our model:

``python data_preparation/convert_to_utterance_format.py --user_id data_preparation/companies_twitter_ids_test.txt --dir_path data_preparation/corpora``

The result of above script is `train.json` and `test.json` files which you can use them for training your model.

