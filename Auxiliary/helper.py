# package import
import datetime
import json


def substring_exists(string_a, string_b):
    # split string a into individual words
    words_in_a = string_a.split()

    # check if any word from string a exists in string b
    for word in words_in_a:
        if word in string_b:
            return True
    return False


def python_datetime_converter(python_time):
    return datetime.datetime.strptime(python_time,"%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y, %H:%M:%S")


def epoch_datetime_converter(epoch_time):
    # epoch time is expected to be in seconds. if dealing with milliseconds, divide by 1000
    return datetime.datetime.fromtimestamp(epoch_time).strftime("%d/%m/%Y, %H:%M:%S")


def clean_json(dict_obj):
    # remove all 'description' keys in the dictionary
    if "description" in dict_obj.keys():
        dict_obj.pop("description")

    return dict_obj


def deduplicate_list(input_list):
    return list(dict.fromkeys(input_list))


def write_to_json(document, content):
    json_string = json.dumps(content)
    json_file = open(document, "w")
    json_file.write(json_string)
    json_file.close()
