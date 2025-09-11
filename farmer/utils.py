import random
import string


def get_error(form):
    errors = dict(form.errors)
    key = tuple(errors.keys())[0]
    error = errors[key]
    key = key.replace('__all__', '')
    if isinstance(error, (tuple, list)):
        return key + ' : ' + error[0]
    tkey = tuple(error.keys())[0]
    tkey = tkey.replace('__all__', '')
    message = key + ' : ' + error[tkey][0]
    return message


def random_string(inital):
    str1 = ''.join((random.choice(string.ascii_letters) for x in range(5)))
    str1 += ''.join((random.choice(string.digits) for x in range(5)))

    sam_list = list(str1)  # it converts the string to list.
    random.shuffle(sam_list)  # It uses a random.shuffle() function to shuffle the string.
    final_string = ''.join(sam_list)
    return inital + "-" + final_string