from parse import *

def parse_vmlist(raw_text):
    # "<inaccessible>" {45fa429e-02bd-4b45-aa47-ffe92e0c5613}
    # "vbox-win7" {4aa6019f-a2c8-431e-9b4c-98f524eb17f0}
    fmt = '"{vbox_name}" {vbox_uuid}'
    out = {}
    for l in raw_text.split("\n"):
        try:
            parsed = parse(fmt, l)
        except Exception as e:
            print(e)
            raise Exception(e)
        out[parsed['vbox_name']] = parsed['vbox_uuid'][1:-1]

    return out

def parse_snapshotlist(raw_text):
    #    Name: snap1 (UUID: 80b017cd-d6bb-4fbb-8aab-a38bb23844f9) *
    fmt = 'Name: {vbox_snapshot_name} {remain}'
    out = []
    for l in raw_text.split("\n"):
        # remove first blank
        blnk_idx = 0
        while True:
            if l[blnk_idx] == " ":
                blnk_idx+=1
            else:
                break
        l = l[blnk_idx:]
        try:
            parsed = parse(fmt, l)
        except Exception as e:
            print(e)
            raise Exception(e)
        out.append(parsed['vbox_snapshot_name'])

    return out

def parse_vminfo(raw_text):
    fmt = 'State: {state} (since {time})'
    out = {
        'state': "",
        'time': ""
    }
    for l in raw_text.split("\n"):
        if "State:" in l:
            while True:
                if "  " in l:
                    l = l.replace("  ", " ")
                else:
                    break
            try:
                parsed = parse(fmt, l)
            except Exception as e:
                print(e)
                raise Exception(e)
            out['state'] = parsed['state']
            out['time'] = parsed['time']
            
    return out