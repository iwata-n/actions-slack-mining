import json
import time
import datetime
import os
import sys
import pandas as pd
from slack_sdk import WebClient

date_from = sys.argv[1]
date_to = sys.argv[2]
group_mention = sys.argv[3]
channel_id = sys.argv[4]
bot_token = sys.argv[5]
user_token = sys.argv[6]

client = WebClient(token=bot_token)

def print_json(j):
  print(json.dumps(j, indent=2, ensure_ascii=False))

def search_message(name, after, before, messages=[], page=1, page_count=None):
  '''
  指定期間内でメンションされたメッセージを全件取得する
  '''
  if page_count is not None and page > page_count:
    return messages

  print(f'name={name}, page={page}, page_count={page_count}')
  time.sleep(3) #search_messagesはTier 2のAPIなので20回/分の制限があるのでとりあえずsleepを入れておく
  
  resp = client.search_messages(token=user_token, query=f'@{name} before:{before} after:{after}', search_exclude_bots=True, sort='timestamp', page=page, count=100)
  page_count = resp.data['messages']['pagination']['page_count']
  m = resp.data['messages']['matches']

  return search_message(name, after, before, messages+m, page+1, page_count)

def mention_frequence(messages):
  '''
  メンションの間隔
  '''
  z = zip(messages, messages[1:])
  count = len(messages)
  if count == 0:
    return datetime.timedelta()
  else:
    return sum([datetime.datetime.fromtimestamp(float(new['ts'])) - datetime.datetime.fromtimestamp(float(old['ts'])) for new, old in z], datetime.timedelta()) / len(messages)

before = date_to
after = date_from

print(f'group={group_mention}')
print(f'after={after}')
print(f'before={before}')

resp = client.usergroups_list()
usergroup = [g['id'] for g in resp.data['usergroups'] if g['handle'] == group_mention][0]

print(f'usergroup={usergroup}')

resp = client.usergroups_users_list(usergroup=usergroup)
users = resp.data['users']
print(f'users={users}')

result = {}
for user in users:
  resp = client.users_info(user=user)
  name = resp.data['user']['name']
  messages = search_message(name=name, after=after, before=before)
  total = len(messages)
  freq = mention_frequence(messages)
  result[name] = {'total': total, 'freq': freq}

print(f'{after}〜{before}')
df = pd.DataFrame.from_dict(result).T
text = '```\n' + str(df.sort_values('freq')) + '\n```'
blocks = [
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "Slackでのメンション数と間隔の集計",
				"emoji": True
			}
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "高頻度で沢山のメンションがある場合は負荷が高い可能性があるのでフォローが必要です"
			}
		},
		{
			"type": "section",
			"fields": [
				{
					"type": "mrkdwn",
					"text": f"*期間:* {after}〜{before}"
				}
			]
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": text
			}
		}
	]

# Slackへの投稿
result = client.chat_postMessage(channel=channel_id, text='test', blocks=blocks)