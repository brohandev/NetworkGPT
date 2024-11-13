import datetime
import json


def python_datetime_converter(python_time):
    return datetime.datetime.strptime(python_time,"%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y, %H:%M:%S")


def epoch_datetime_converter(epoch_time):
    # epoch time is expected to be in seconds. if dealing with milliseconds, divide by 1000
    return datetime.datetime.fromtimestamp(epoch_time).strftime("%d/%m/%Y, %H:%M:%S")


def generate_id_list(obj_dict_list):
    return [obj_dict["id"] for obj_dict in obj_dict_list]


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


if __name__ == '__main__':
    print(epoch_datetime_converter(1694659961000/1000))
    print(python_datetime_converter("2023-10-04T06:30:12Z"))
