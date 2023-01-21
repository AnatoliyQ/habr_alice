import json
import logging
import os

import requests
from flask import Flask, request
from bs4 import BeautifulSoup
from collections import deque

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

isBest = False
isNew = False

pagesStore = {}

tempPostStorage = ''
pageIndexFrom = 0


@app.route('/post', methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)

    logging.info('Response: %r', request.json)

    return json.dumps(response)


def handle_dialog(req, res):
    if req['session']['new']:
        res['response']['text'] = 'Привет! Я могу за тебя читать хабр. Выбери что желаешь:  лучшее или новое '
        res['response']['buttons'] = get_hi_suggests()
        return

    if req['request']['original_utterance'].lower() in [
        'лучшее'
    ]:
        global isBest
        global isNew
        isBest = True
        isNew = False
        res['response']['text'] = 'За какое время хотите лучшее? За сутки, неделю, месяц, год или все время  '
        res['response']['buttons'] = get_best_suggests()
        return

    if req['request']['original_utterance'].lower() in [
        'новое'
    ]:
        isNew = True
        isBest = False
        res['response']['text'] = 'От какого рейтинга хотите подборку? 0 10 25 50 100'
        res['response']['buttons'] = get_new_suggests()
        return

    if (isBest == True):
        if req['request']['original_utterance'].lower() in [
            'сутки',
            'за сутки',
            'лучшее за сутки'
        ]:
            clearGlobalState()
            dailyRaw = getBestForTime('daily')

            for val in dailyRaw.values():
                pagesStore[val['id']] = val['titleHtml'].lower()

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В лучшем за сутки следующие статьи \n' + readTitlePages()

            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'дальше статьи'
        ]:

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В лучшем за сутки следующие статьи \n' + readTitlePages()
            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'дальше текст'
        ]:
            text = getNextTextForReading()
            if (len(text) == 0):
                text = 'Статья закончилась'
            res['response']['text'] = text
            res['response']['buttons'] = get_next_text_suggests()
            return

        if req['request']['original_utterance'] in pagesStore.values():
            post = getPostById(getPostIdByValue(req['request']['original_utterance']))

            words = post.split(".")

            text = getTextForReading(deque(words))

            res['response']['text'] = text
            res['response']['buttons'] = get_next_text_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'неделю',
            'неделя',
            'за неделю',
            'лучшее за неделю',
        ]:
            clearGlobalState()
            weekly = getBestForTime('weekly')

            for val in weekly.values():
                pagesStore[val['id']] = val['titleHtml'].lower()

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В лучшем за неделю следующие статьи \n' + readTitlePages()

            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'месяц',
            'за месяц',
            'лучшее за месяц',
        ]:
            clearGlobalState()
            monthly = getBestForTime('monthly')

            for val in monthly.values():
                pagesStore[val['id']] = val['titleHtml'].lower()

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В лучшем за месяц следующие статьи \n' + readTitlePages()

            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'год',
            'за год',
            'лучшее за год',
        ]:
            clearGlobalState()
            yearly = getBestForTime('yearly')

            for val in yearly.values():
                pagesStore[val['id']] = val['titleHtml'].lower()

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В лучшем за год следующие статьи \n' + readTitlePages()
            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'все время',
            'за все время',
            'лучшее за все время',
        ]:
            clearGlobalState()
            alltime = getBestForTime('alltime')

            for val in alltime.values():
                pagesStore[val['id']] = val['titleHtml'].lower()

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В лучшем за все время следующие статьи \n' + readTitlePages()

            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

    if (isNew == True):
        if req['request']['original_utterance'].lower() in [
            'ноль',
            'нуль',
            'зеро'
        ]:
            clearGlobalState()
            zeroRaw = getNewByRaiting(0)

            for val in zeroRaw.values():
                pagesStore[val['id']] = val['titleHtml'].lower()

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В новом с рейтингом > 0 следующие статьи \n' + readTitlePages()

            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'десять',
            'от десяти',
            'десяточка'
        ]:
            clearGlobalState()
            tenRaw = getNewByRaiting(10)

            for val in tenRaw.values():
                pagesStore[val['id']] = val['titleHtml'].lower()

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В новом с рейтингом > 10 следующие статьи \n' + readTitlePages()

            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'двадцать пять',
            'четвертной'
        ]:
            clearGlobalState()
            raw = getNewByRaiting(25)

            for val in raw.values():
                pagesStore[val['id']] = val['titleHtml'].lower()

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В новом с рейтингом > 25 следующие статьи \n' + readTitlePages()

            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'пятьдесят',
            'полтинник'
        ]:
            clearGlobalState()
            raw = getNewByRaiting(50)

            for val in raw.values():
                pagesStore[val['id']] = val['titleHtml'].lower()

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В новом с рейтингом > 50 следующие статьи \n' + readTitlePages()

            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'сто',
            'сотня',
            'соточка'
        ]:
            clearGlobalState()
            raw = getNewByRaiting(100)

            for val in raw.values():
                pagesStore[val['id']] = val['titleHtml'].lower()

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В новом с рейтингом > 100 следующие статьи \n' + readTitlePages()

            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'дальше статьи'
        ]:

            if pageIndexFrom == -1:
                text = 'Все статьи прочитаны'
            else:
                text = 'Для продолжения чтения списка скажите далее. В лучшем за сутки следующие статьи \n' + readTitlePages()
            res['response']['text'] = text
            res['response']['buttons'] = get_next_pages_suggests()
            return

        if req['request']['original_utterance'].lower() in [
            'дальше текст'
        ]:
            text = getNextTextForReading()
            if (len(text) == 0):
                text = 'Статья закончилась'
            res['response']['text'] = text
            res['response']['buttons'] = get_next_text_suggests()
            return

        if req['request']['original_utterance'] in pagesStore.values():
            post = getPostById(getPostIdByValue(req['request']['original_utterance']))

            words = post.split(".")

            text = getTextForReading(deque(words))

            res['response']['text'] = text
            res['response']['buttons'] = get_next_text_suggests()
            return

    res['response']['text'] = 'Извините, я не знаю комманду "%s"' % (
        req['request']['original_utterance']
    )

    if req['request']['original_utterance'].lower() in [
        'выход',
        'все',
        'хватит',
    ]:
        res['response']['text'] = 'Спасибо что воспользовались моим навыком! До свидания!'
        res['response']['end_session'] = True
        return


def get_hi_suggests():
    suggests = [
        {'title': 'лучшее', 'hide': True},
        {'title': 'новое', 'hide': True}
    ]
    return suggests


def get_best_suggests():
    suggests = [
        {'title': 'сутки', 'hide': True},
        {'title': 'неделя', 'hide': True},
        {'title': 'месяц', 'hide': True},
        {'title': 'год', 'hide': True},
        {'title': 'все время', 'hide': True}
    ]
    return suggests


def get_new_suggests():
    suggests = [
        {'title': 'ноль', 'hide': True},
        {'title': 'десять', 'hide': True},
        {'title': 'двадцать пять', 'hide': True},
        {'title': 'пятьдесят', 'hide': True},
        {'title': 'сто', 'hide': True}
    ]
    return suggests


def get_next_pages_suggests():
    suggests = [
        {'title': 'дальше статьи', 'hide': True}
    ]
    return suggests


def get_next_text_suggests():
    suggests = [
        {'title': 'дальше текст', 'hide': True},
        {'title': 'новое', 'hide': True},
        {'title': 'лучшее', 'hide': True}
    ]
    return suggests


def readTitlePages():
    result = ''
    global pageIndexFrom

    values = list(pagesStore.values())

    for item in values[pageIndexFrom: len(values)]:
        if (len(result) + len(item)) < 900:
            result = result + "\n" + item
        else:
            pageIndexFrom = values.index(item)
            return result

    pageIndexFrom = -1
    return result


def getPostIdByValue(value):
    return list(pagesStore.keys())[list(pagesStore.values()).index(value)]


def getTextForReading(deq):
    result = ''
    while len(deq) > 0:
        if (len(result) + len(deq[0])) < 900:
            result = result + "." + deq.popleft()
        else:
            global tempPostStorage
            tempPostStorage = deq
            return result

    return result


def getNextTextForReading():
    result = ''
    while len(tempPostStorage) > 0:
        if (len(result) + len(tempPostStorage[0])) < 900:
            result = result + "." + tempPostStorage.popleft()
        else:
            return result

    return result


# daily
# weekly
# monthly
# yearly
# alltime
def getBestForTime(time):
    r = requests.get('https://habr.com/kek/v2/articles/?period={}&sort=date&fl=ru&hl=ru&page=1'.format(time)).text
    data = json.loads(r)

    items = data['articleRefs']

    return items


# 0 10 25 50 100
def getNewByRaiting(raiting):
    r = requests.get('https://habr.com/kek/v2/articles/?sort=rating&score={}&fl=ru&hl=ru&page=1'.format(raiting)).text
    data = json.loads(r)

    items = data['articleRefs']

    return items


def clearGlobalState():
    global tempPostStorage
    global pageIndexFrom

    tempPostStorage = ''
    pageIndexFrom = 0


def getPostById(id):
    url = "https://habr.com/kek/v2/articles/{}/?fl=ru%2Cen&hl=ru".format(id)

    r = requests.get(url)

    data = json.loads(r.text)

    title = data['titleHtml']
    content = data['textHtml']

    root = BeautifulSoup(content, 'html5lib')

    div = root.select_one('div')

    for x in div.select('code'):
        x.decompose()

    text = root.get_text()

    lines = (line.strip() for line in text.splitlines())

    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    text = '\n'.join(chunk for chunk in chunks if chunk)

    return text


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)
