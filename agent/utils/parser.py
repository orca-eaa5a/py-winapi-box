from parse import *
import json

def parsing(chunk):
    lines = chunk.split("\n")[:-1]
    result = {
        'api_name': '',
        'args': [],
        'ret': ''
    }
    if len(lines) == 1:
        if lines[0][0] == "[":
            parsed = parse("[{proc_name}] [{pid}] {api_name} ({remain}", lines[0])
            result['api_name'] = parsed['api_name']
        else:
            raise Exception("WTF")
        
        pass
    else:
        if lines[0][0] == "[":
            parsed = parse("[{proc_name}] [{pid}] {api_name} (", lines[0])
            result['api_name'] = parsed['api_name']
        else:
            raise Exception("WTF")
        arg = {
            'type': '',
            'value': ''
        }
        for l in lines[1:-1]:
            parsed = parse("        {arg_type} {remain} = {value}", l)
            result['args'].append({
                'type':parsed['arg_type'],
                'value':parsed['value']
            })
    parsed = parse("{remain} -> {ret} [{remain2}", lines[-1])
    result['ret'] = parsed['ret']
    
    return result

def parse_xlogger_result(path):
    result = {
        'apis':[]
    }
    with open(path, 'rt') as f:
        chunk = ""
        chunk_start = False
        while True:
            l = f.readline()
            if not l:
                break
            if l == "\n":
                if chunk_start == True:
                    res = parsing(chunk)
                    result['apis'].append(res)
                    chunk = ""
                    chunk_start = False
                else:
                    # ignore empty line
                    continue
            else:
                if chunk_start == False:
                    chunk_start = True
                chunk += l
    
    return result

if __name__ == "__main__":
    result = {
        'list':[]
    }
    with open('log.txt', 'rt') as f:
        chunk = ""
        chunk_start = False
        while True:
            l = f.readline()
            if not l:
                break
            if l == "\n":
                if chunk_start == True:
                    # do parsing
                    res = parsing(chunk)
                    result['list'].append(res)
                    chunk = ""
                    chunk_start = False
                else:
                    continue
            else:
                if chunk_start == False:
                    chunk_start = True
                chunk += l

    with open('result.json', 'wt') as f:
        json.dump(result, f, indent=4)