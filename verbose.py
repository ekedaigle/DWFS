import functools
import inspect
import sys

print_func = sys.stdout.write

def make_str(arg):
    if isinstance(arg, str):
        if len(arg) > 100:
            return '{} bytes'.format(len(arg))
        else:
            return '\'{}\''.format(arg)
    else:
        return str(arg)

def verbose(func):

    @functools.wraps(func)
    def func_verbose(*args, **kwargs):
        str_list = []
        str_list.append('{}('.format(func.__name__))

        arg_names = inspect.getargspec(func).args
        is_method = bool(arg_names and arg_names[0] == 'self')

        for i in range(len(args)):
            if i == 0 and is_method:
                continue

            str_list.append(make_str(args[i]))

            if i != len(args) - 1:
                str_list.append(', ')

        str_list.append(') -> ')
        
        ret = func(*args, **kwargs)
        str_list.append(make_str(ret))
        print_func(''.join(str_list))
        return ret

    return func_verbose
