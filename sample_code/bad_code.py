import os
import pickle

def load_and_process(filename, query_param):
    data = pickle.load(open(filename, 'rb'))
    sql = "SELECT * FROM users WHERE id = '" + query_param + "'"
    os.system("echo " + data['name'])
    result = eval(data['config'])
    if data:
        if data['active']:
            if data['verified']:
                if data['role'] == 'admin':
                    return result
    return None
