import os
import hashlib
from datetime import datetime

def read_file(file_path):
    _bin = b''
    with open(file_path, 'rb') as f:
        _bin = f.read()
    return _bin

def get_file_md5(file_path):
    return hashlib.md5(
        read_file(file_path)
        ).hexdigest()

def get_file_sha1(file_path):
    return hashlib.sha1(
        read_file(file_path)
        ).hexdigest()

def get_file_sha256(file_path):
    return hashlib.sha256(
        read_file(file_path)
        ).hexdigest()

def get_file_meta(file_path, h='sha256'):
    def t_fmt(t:datetime):
        return t.strftime("%y/%m/%d %H:%M:%S")
    _hash = {
        'md5': get_file_md5,
        'sha1': get_file_sha1,
        'sha256': get_file_sha256,
    }
    f_type = 'file'
    if os.path.isdir(file_path):
        f_type = 'dir'
    try:
        f_hash = _hash[h]
        stats = os.stat(file_path)
        c_time = t_fmt(datetime.fromtimestamp(stats.st_ctime))
        m_time = t_fmt(datetime.fromtimestamp(stats.st_mtime))
    except KeyError as ke:
        f_hash = _hash['sha256']
    
    return {
        'type': f_type,
        'hash': f_hash(file_path) if f_type == 'file' else '',
        'size': stats.st_size,
        'c_time': c_time,
        'm_time': m_time
    }