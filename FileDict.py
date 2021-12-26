import os
import pickle

dir_name = "data"

def get_file_path(name):
    return os.path.join(dir_name, name + '.pkl')


def save_obj(obj, name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    with open(get_file_path(name), 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)


def load_obj(name):
    with open(get_file_path(name), 'rb') as f:
        return pickle.load(f)
