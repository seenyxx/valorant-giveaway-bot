import requests

port = '8888'
host = 'http://localhost:{}'.format(port)

def get_valorant_giveaways():
    req = requests.get('{}/twitter/val-giveaway'.format(host))
    return req.json()
