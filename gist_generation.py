"""
Copyright 2020 ibx34

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import random
import string
from datetime import datetime
import requests
import config
from logger import logging


async def gist_invalidation(token, user, guild, channel, message_content):
    logging.info(f"Bot started creating gist for token: {token}")
    id = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(32)])
    try:
        GITHUB_API = "https://api.github.com"
        API_TOKEN = config.github_api_token

        url = GITHUB_API + "/gists"

        headers = {"Authorization": "token %s" % API_TOKEN}
        params = {"scope": "gist"}
        payload = {
            "description": f"Token Invalidation",
            "public": True,
            "files": {
                f"Token Invalidation - {id}": {
                    "content": f"{token}"
                }
            },
        }
        res = requests.post(url, headers=headers, params=params, data=json.dumps(payload))

        j = json.loads(res.text)
        logging.info(f"Bot finished creating gist. Link: https://gist.github.com/ibx34/{j['id']}")
        data = {"url": f"https://gist.github.com/wrenchboat/{j['id']}","id": id}
        return data

    except Exception as err:
        logging.fail(f"Error occured while creating gist. {err}")
