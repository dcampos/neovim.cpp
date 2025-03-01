#!/usr/bin/python
# -*- coding: utf-8 -*-

from jinja2 import Environment, FileSystemLoader
import msgpack, sys, os, subprocess
import re

class InvalidType(Exception): 
    pass

class NativeType:
    def __init__(self, name, expect_ref = False):
        self.name = name
        self.expect_ref = expect_ref

REMAP_T = {
    'ArrayOf(Integer, 2)': NativeType('std::vector<Integer>', True),
    'Boolean': NativeType('bool'),
    'Float': NativeType('float'),
    'String': NativeType('std::string', True),
    'Array': NativeType('std::vector<Variant>', True),
    'Dictionary': NativeType('std::map<std::string, Variant>', True),
    'void': NativeType('void'),
    'Window': NativeType('Window'),
    'Buffer': NativeType('Buffer'),
    'Tabpage': NativeType('Tabpage'),
    'Integer': NativeType('Integer'),
    'Object': NativeType('Object', True)
}

def convert_type_to_native(nvim_t, enable_ref_op):
    array_of = r'ArrayOf\(\s*(\w+)\s*\)'
    
    obj = re.match(array_of, nvim_t)
    if obj:
        ret = 'std::vector<%s>' % convert_type_to_native(obj.groups()[0], False)
        return 'const ' + ret + '&' if enable_ref_op else ret
    
    if nvim_t in REMAP_T:
        native_t = REMAP_T[nvim_t]
        return 'const ' + native_t.name + '&' if enable_ref_op and native_t.expect_ref else native_t.name
    else:
        print("unknown nvim type name: " + str(nvim_t))
        raise InvalidType()
    
    #TODO: implement error handler
    #return nvim_t

def main():
    env = Environment(loader=FileSystemLoader('templates', encoding='utf8'))
    tpl = env.get_template('nvim.hpp')

    api_info = subprocess.check_output(["nvim", '--api-info'])
    unpacked_api = msgpack.unpackb(api_info)

    functions = []
    for f in unpacked_api['functions']:

        d = {}
        d['name'] = f['name']

        try:
            d['return'] = convert_type_to_native(f['return_type'], False)
            d['args'] = [{'type': convert_type_to_native(arg[0], True), 'name': arg[1]} for arg in f['parameters']]
            functions.append(d)
        except InvalidType as e:
            print("invalid function = " + str(f))

    api = tpl.render({'functions': functions})
    #print api.encode('utf-8')

    with open(os.path.join("./gen", "nvim.hpp"), 'w') as f:
        f.write(api)

if __name__ == '__main__':
    main()

