import json
import requests
import time
import urllib
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import mlab
from dbhelper import DBHelper

db = DBHelper()

import exchange
pol = exchange.poloniex(None, None)

pairs = sorted(pol.returnTicker().keys())
currs = sorted([i.split("_")[1] for i in pairs if i.startswith("BTC")])


TOKEN = "paste_token_here"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)

f = open("users.txt", 'r')
users = {x.split(',')[0]:x.split(',')[1].rstrip() for x in f}
f.close

commands = {
    '/start': "Best bot ever. Send /help to get help",
    '/help': "/cur displays all available currencies.\n" + \
            "/pairs displays all available pairs.\n" + \
            "/btc returns BTC/USDT\n" + \
            "/abb 'some_coin' returns coin description\n" + \
            "/add 'coin' 'price' saves your order\n" + \
            "/del 'coin' removes your order\n" + \
            "/show returns your orders\n" + \
            "Send currency code or pair to get its price",
    '/cur': " ".join(currs),
    '/pairs': " ".join(pairs)
}

abbs = open("abbreviations.csv",'r')
abbs = {l.split(',')[0]:l.split(',')[1].rstrip() for l in abbs}


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    try:
        js = json.loads(content)
    except:
        js = {"results": ""}
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=300"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def echo_all(updates):
    for update in updates["result"]:
        chat = update["message"]["chat"]["id"]
        if str(chat) not in users.keys():
            users[str(chat)] = update["message"]["from"]["username"]
            f = open("users.txt", 'w')
            f.write("\n".join([",".join(x) for x in users.items()]))
            f.close()
        if "edited_message" in update:
            continue
        if 'text' in update['message']:
            intext = update['message']['text']
            if intext.startswith("/"):
                if intext == "/btc":
                    response = pol.returnTicker()["USDT_BTC"]
                    text = "BTC/USDT: " + str(int(round(float(response['last'])))) + "$ ("+str(float(response['percentChange'])*100)+"%)"
                elif intext.startswith("/abb"):
                    ab = intext.split(" ")
                    if len(ab)>1:
                        ab = ab[1].upper()
                        if ab in abbs.keys():
                            text = abbs[ab]
                        else:
                            text = "No information about %s" % ab
                    else:
                        text = ", ".join(["--".join(l) for l in abbs.items()])
                elif intext.startswith("/add"):
                    tmp = intext.split(" ")
                    if len(tmp)<3:
                        text = "Some arguments missing"
                    else:
                        db.add_item(tmp[1], tmp[2], chat)
                        text = "Success"
                elif intext.startswith("/del"):
                    tmp = intext.split(" ")
                    if len(tmp)<2:
                        text = "Some arguments missing"
                    else:
                        db.delete_item(tmp[1], chat)
                        text = "Success"
                elif intext.startswith("/show"):
                    try:
                        text = "\n".join(db.get_items(chat))
                    except:
                        text = "You have no open orders"
                else:
                    if intext in commands.keys():
                        text = commands[intext]
                    else:
                        text = "No such command.\n"+commands['/help']
            else:
                if intext.upper() in currs:
                    intext = intext.upper()
                    response = pol.returnTicker()["BTC_"+intext]
                    text = intext+"/BTC: " + response['last'] + " ("+str(float(response['percentChange'])*100)+"%)"
                else:
                    if "/" in intext:
                        intext = intext.upper()
                        response = pol.returnTicker()[intext.replace("/","_")]
                        text = intext + ": " + response['last'] + " ("+str(float(response['percentChange'])*100)+"%)"
                    else:
                        text = "Illegal request"
        else:
            text = 'Unknown action. Please, connect with mega_mad'
        send_message(text, chat)


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def send_message(text, chat_id):
    text = urllib.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)

def get_depth(pair):
    depth = pol.returnOrderBook(pair)
    asks = pd.DataFrame.from_dict(depth["asks"])
    bids = pd.DataFrame.from_dict(depth["bids"])
    plt.hist([bids, asks], bins=100, cumulative=[-1,1], histtype='stepfilled', color=["green","red"])
    plt.savefig("depth.png")

def main():
    db.setup()
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if "result" in updates:
            if len(updates["result"]) > 0:
                last_update_id = get_last_update_id(updates) + 1
                echo_all(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    main()
