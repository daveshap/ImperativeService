import requests
from time import time
from uuid import uuid4
import numpy as np
import re
import os
import openai
from time import time,sleep


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


openai.api_key = open_file('openaiapikey.txt')
service_name = 'heuristic_imperatives'
tempo = 30


def gpt3_completion(prompt, engine='text-davinci-002', temp=0.7, top_p=1.0, tokens=1000, freq_pen=0.0, pres_pen=0.0, stop=['asdfasdf', 'asdasdf']):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
    while True:
        try:
            response = openai.Completion.create(
                engine=engine,
                prompt=prompt,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,
                stop=stop)
            text = response['choices'][0]['text'].strip()
            #text = re.sub('\s+', ' ', text)
            filename = '%s_gpt3.txt' % time()
            save_file('gpt3_logs/%s' % filename, prompt + '\n\n==========\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(1)


def get_embedding(payload):  # payload is a list of strings
    # payload example: ['bacon bacon bacon', 'ham ham ham']
    # response example:  [{'string': 'bacon bacon bacon', 'vector': '[1, 1 ... ]'}, {'string': 'ham ham ham', 'vector': '[1, 1 ... ]'}]
    # embedding is already rendered as a JSON-friendly string
    url = 'http://127.0.0.1:999'  # currently the USEv5 service, about 0.02 seconds per transaction!
    response = requests.request(method='POST', url=url, json=payload)
    return response.json()


def nexus_send(payload):  # REQUIRED: content
    url = 'http://127.0.0.1:8888/add'
    payload['time'] = time()
    payload['uuid'] = str(uuid4())
    payload['content'] = content_prefix + payload['content']
    embeddings = get_embedding([payload['content']])
    payload['vector'] = embeddings[0]['vector']
    payload['service'] = service_name
    response = requests.request(method='POST', url=url, json=payload)
    print(response.text)


def nexus_search(payload):
    url = 'http://127.0.0.1:8888/search'
    response = requests.request(method='POST', url=url, json=payload)
    return response.json()


def nexus_bound(payload):
    url = 'http://127.0.0.1:8888/bound'
    response = requests.request(method='POST', url=url, json=payload)
    #print(response)
    return response.json()


def nexus_save():
    url = 'http://127.0.0.1:8888/save'
    response = requests.request(method='POST', url=url)
    print(response.text)


def save_and_send(content, prefix, tag):
    filename = '%s_%s.txt' % (time(), tag)
    content = prefix + content
    save_file('logs/' + filename, content)
    nexus_send({'content': content})


if __name__ == '__main__':
    while True:
        # get recent memories
        payload = {'lower_bound': time() - tempo, 'upper_bound': time()}
        recent = nexus_bound(payload)
        lines = [i['content'] for i in recent]
        textblock = ' '.join(lines)
        # TODO get relevant older memories too
        # reduce suffering
        prompt = open_file('reduce_suffering_brainstorm.txt').replace('<<BLOCK>>', textblock)
        suffering = gpt3_completion(prompt)
        save_and_send(suffering, 'Ideas to reduce suffering: ', 'suffering')
        # increase prosperity
        prompt = open_file('increase_prosperity_brainstorm.txt').replace('<<BLOCK>>', textblock)
        prosperity = gpt3_completion(prompt)
        save_and_send(prosperity, 'Ideas to increase prosperity: ', 'prosperity')
        # increase understanding
        prompt = open_file('increase_understanding_brainstorm.txt').replace('<<BLOCK>>', textblock)
        understanding = gpt3_completion(prompt)
        save_and_send(understanding, 'Ideas to increase understanding: ', 'understanding')
        # curiosity (ask questions)
        prompt = open_file('increase_understanding_questions.txt').replace('<<BLOCK>>', textblock)
        questions = gpt3_completion(prompt)
        save_and_send(questions, 'Questions to increase understanding: ', 'questions')
        # wait
        sleep(tempo)

'''
TODO stuff
- suffering should also evaluate current situation "identify suffering, causes, predict short term and long term outcomes" etc
- prosperity should also think short and long term
- understanding should also include curiosity

Key dispositions:
- time scale (short, long term)
- 

'''