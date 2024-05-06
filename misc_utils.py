"""
====================================
Miscellaneous tools for DicomTreeQT5
====================================
"""
# Author: AC Chamberlain


def get_dot_attr(obj, att_name) -> str:
    """
    Gets the value of the named dotted attribute in nested classes
    a = get_dot_attr(x, 'y.z') is equivalent to a = x.y.z
    Also caters for lists of classes
    :param
    obj: starting object to get attribute from
    att_name: string with full dotted path to the attribute
    :return: string with attribute value
    """
    # split the dotted name into a path to follow
    path = att_name.split('.')
    for part in path:
        parts = part.split('[')
        if len(parts) > 1:
            sequence_num = int(parts[1].replace(']', "")) - 1
            obj = obj[sequence_num]
        else:
            obj = getattr(obj, part)
    return obj


def set_dot_attr(obj, att_name, value):
    """
    Sets the value of the named dotted attribute in nested classes
    set_dot_attr(x, 'y.z', a) is equivalent to x.y.z = a
    Also caters for lists of classes
    :param
    obj: starting object to get attribute from
    att_name: string with full dotted path to the attribute
    value: new value for the attribute
    :return: none
    """
    # split the dotted name into a path to follow
    path = att_name.split('.')
    tag_name = path[-1]
    del(path[-1])
    for part in path:
        parts = part.split('[')
        if len(parts) > 1:
            sequence_num = int(parts[1].replace(']', "")) - 1
            obj = obj[sequence_num]
        else:
            obj = getattr(obj, part)
    setattr(obj, tag_name, value)
    return


def del_dot_attr(obj, att_name):
    """
    Deletes the value of the named dotted attribute in nested classes
    del_dot_attr(x, 'y.z) is equivalent to del x.y.z
    Also caters for lists of classes
    :param
    obj: starting object to get attribute from
    att_name: string with full dotted path to the attribute
    """
    # split the dotted name into a path to follow
    path = att_name.split('.')
    for part in path[:-1]:
        parts = part.split('[')
        if len(parts) > 1:
            sequence_num = int(parts[1].replace(']', "")) - 1
            obj = obj[sequence_num]
        else:
            obj = getattr(obj, part)
    delattr(obj,path[-1])


def text_to_tag(tag_text: str) -> tuple:
    tag_element = tag_keyword = tag_vr = tag_value = ''
    tag_group = tag_text[1:5]
    if tag_group.isnumeric(): # item is a tag
        tag_group = '0x' + tag_group
        tag_element = '0x' + tag_text[7:11]
        tag_vr = tag_text.split(':')[0][-2:]
        tag_keyword = tag_text.split(':')[0].split(')')[1][:-2].strip()
        tag_value = tag_text.split(':')[1].strip()
    else:                     # item is a sequence
        tag_keyword = tag_text.split(':')[0].strip()
    return tag_group, tag_element, tag_keyword, tag_vr, tag_value



