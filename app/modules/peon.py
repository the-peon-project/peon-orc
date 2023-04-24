import sys
import json
import random

sys.path.insert(0,'/app')

dictionary = json.load(open("/app/dictionary.json", 'r'))

def get_warcamp_name():
    prefix = dictionary['server_names']['prefix']
    suffix = dictionary['server_names']['suffix']
    return (random.choice(prefix) + random.choice(suffix))

if __name__ == "__main__":
    print(get_warcamp_name())