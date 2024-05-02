"""
====================================
Miscellaneous tools for DicomTreeQT5
====================================
"""
# Author: AC Chamberlain


def get_dot_attr(obj, att_name) -> str:
    """
    Gets the value of the named dotted attribute in nested classes
    a= get_dot_attr('x.y.z) is equivalent to a = x.y.z
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
            sequence_str = parts[0]
            sequence_num = int(parts[1].replace(']', "")) - 1
            sequence = getattr(obj, sequence_str)
            obj = sequence[sequence_num]
        else:
            obj = getattr(obj, part)
    return obj


def set_dot_attr(obj, att_name, value):
    """
    Sets the value of the named dotted attribute in nested classes
    a= get_dot_attr('x.y.z) is equivalent to a = x.y.z
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
            sequence_str = parts[0]
            sequence_num = int(parts[1].replace(']', "")) - 1
            sequence = getattr(obj, sequence_str)
            obj = sequence[sequence_num]
        else:
            obj = getattr(obj, part)
    setattr(obj, tag_name, value)
    return


def del_dot_attr(obj, att_name):
    """
    Gets the value of the named dotted attribute in nested classes
    a= get_dot_attr('x.y.z) is equivalent to a = x.y.z
    :param
    obj: starting object to get attribute from
    att_name: string with full dotted path to the attribute
    :return: string with attribute value
    """
    # split the dotted name into a path to follow
    path = att_name.split('.')
    for part in path[:-1]:
        parts = part.split('[')
        if len(parts) > 1:
            sequence_str = parts[0]
            sequence_num = int(parts[1].replace(']', "")) - 1
            sequence = getattr(obj, sequence_str)
            obj = sequence[sequence_num]
        else:
            obj = getattr(obj, part)
    delattr(obj,path[-1])


