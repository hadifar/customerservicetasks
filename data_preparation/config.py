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

class Config:
    """
    Put your own api and security key
    read more: https://developer.twitter.com/en
    """
    API_KEY = "AIzxwkUA6qPw5VzvacCiyAhRq"
    API_SEC_KEY = "D6z1t1F2fmpDk9Ek34u5SFNejDs29Dy36PhlxlO10sdhSasbPc"
    ACCESS_TOKEN = "1271345023821459456-HaPrEMtVZoUdAk6YbZjWSCA17uvDbj"
    ACCESS_TOKEN_SEC = "SW0wmBPXe6AoMMjZW1SIq1vZ5BDv8HozXtyWCqh95wNfX"

def get_config(name):
    if name == 'myself':
        return Config
    else:
        raise Exception("credential not found!")
