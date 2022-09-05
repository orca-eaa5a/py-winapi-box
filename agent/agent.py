
"""
xLogger.exe --apis-dir "..\\WinApi" --headers-dir "..\\WinAPI\\headers"  -c C:\\Windows\\System32\\notepad.exe -l "..\..\log.txt"
"""
import os
from io import BytesIO
import socket
import argparse
import json
import subprocess
from textwrap import dedent
from time import sleep, time
from threading import Thread
import subprocess
from utils.agent_logger import AgentLogger
from utils.parser import parse_xlogger_result
from utils.meta import get_file_meta

class Agent(object):
    class ActionID:
        INIT = 0
        CREATE_FILE=1
        CREATE_PROCESS=2
        GET_RESULT=3
        HALT=4
        GET_FILES_LIST=5
        EXTRACT_FILE=6

    def __init__(self, server_ip, port) -> None:
        self.logger = AgentLogger().logger
        self.launch_path = os.path.abspath(os.path.join(__file__, os.pardir))
        self.server_ip = server_ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.default_folder = os.path.join(os.getenv('UserProfile'), 'Desktop')
        self.log_dir = self.launch_path
        self.apilog_ext = ".api"
        pass

    def connect_to_server(self):
        retry_cnt = 0
        self.sock.settimeout(10.0)
    
        while 10 > retry_cnt:
            try:
                self.sock.connect((self.server_ip, self.port))
                self.sock.settimeout(None)
                return True
            except socket.timeout as te:
                self.logger.critical("Connection failed to server %s:%d with error > %s" % (self.server_ip, self.port, te))
                raise Exception('Connection timeout %s' % te)
            
            except ConnectionRefusedError as ce:
                retry_cnt += 1
                self.logger.error("Can't find server %s:%d with error > %s" % (self.server_ip, self.port, ce))
                self.logger.debug("Wait for server starting... (retry : %d)" % retry_cnt)
                sleep(10)
                pass

            except Exception as e:
                self.logger.critical("Unknown error occured with error > " % e)
                raise Exception('Unknown error %s' % e)
        
        return False

    def send_json_wrapper(self, data):
        EOM = b'orca.eaa5a'
        try:
            _data = json.dumps(data).encode("utf-8")
            _data += EOM
            self.sock.send(_data)
        except json.JSONDecodeError:
            self.logger.error("json parsing error > %s" % str(data))
        except Exception as e:
            self.logger.error("send data faield with error > %s" % e)

    def launch(self):
        if not self.connect_to_server():
            self.logger.critical("Connection to server failed.. %s:%d" % (self.server_ip, self.port))
            raise Exception("Connect to server failed.. %s:%d" % (self.server_ip, self.port))
        self.logger.info("Server connected!! (%s)" % self.server_ip)
        """
        alert to server that agent is active
        """
        server_init_msg = {
            "ip": self.sock.getsockname()[0],
            "_timestap": time(),
            "action": Agent.ActionID.INIT
        }
        self.send_json_wrapper(
            server_init_msg
        )
        
        self.listener()
        self.sock.close()

    def listener(self):
        self.logger.info("Listener Started!")
        while True:
            try:
                data = self.sock.recv(1024).decode("utf-8")
                if not data:
                    break
                body = json.loads(data)
                self.action_handler(
                    action_id=body['act_id'], 
                    data=body['data']
                )
            except json.decoder.JSONDecodeError as de:
                self.logger.error("Invalid data recieved with error > %s" % de)
            except ConnectionResetError as cre:
                self.logger.critical("Server %s connection closed" % self.sock.getsockname()[0])
                break
            except Exception as e:
                self.logger.critical("Unknown error occured with error > %s" % e)
                break

    def action_handler(self, action_id, data):
        self.logger.debug("action_handler called with action %d" % action_id)
        if action_id == Agent.ActionID.CREATE_FILE:
            file_sz = data['file_sz']
            recv_sz = 0
            _bin = b''
            while True:
                recv_bin = self.sock.recv(1024)
                _bin += recv_bin
                recv_sz += len(recv_bin)
                if not _bin:
                    break
                if recv_sz >= file_sz:
                    break

            path = os.path.join(self.default_folder, data['fname'])
            try:
                with open(path, 'wb') as f:
                    f.write(_bin)
            except Exception as PermissionError:
                self.logger.critical("Unable to write file to %s" % path)
                return -1

            self.send_json_wrapper(
                {
                    "ip": self.sock.getsockname()[0],
                    "_timestamp": time(),
                    "action": action_id,
                    "success": True,
                    "target": data['fname'],
                    "file_sz": len(_bin)
                }
            )

        elif action_id == Agent.ActionID.CREATE_PROCESS:
            def check_platform(_bin):
                stream = BytesIO(_bin)
                e_magic = stream.read(2)
                stream.seek(60)
                e_lfanew = stream.read(4)
                pe_start_off = int.from_bytes(e_lfanew, byteorder="little")
                stream.seek(pe_start_off)
                stream.seek(4, 1) # skip signature
                stream.seek(20, 1) # IMAGE_FILE_HEADER
                magic = int.from_bytes(stream.read(2), byteorder="little")
                if magic == 0x10b:
                    return '32bit'
                elif magic == 0x20b:
                    return '64bit'
                else:
                    return 'unk'

            path = self.default_folder
            if not 'fname' in data:
                self.logger.error('Invalid request: fname is needed')
                return -1
            path = os.path.join(self.default_folder, data['fname'])
            
            # check target file is x86 or x64
            _bin = b''
            try:
                with open(path, 'rb') as f:
                    _bin = f.read(1024)
            except FileNotFoundError as fne:
                self.logger.error("Can't find target file to launch : %s" % path)
                self.send_json_wrapper(
                    {
                        "ip": self.sock.getsockname()[0],
                        "_timestamp": time(),
                        "action": action_id,
                        "success": False,
                        "target": data['fname'],
                        "err": "file does not exist"
                    }
                )
                return -1
            command_line = ""

            log_path = os.path.join(self.log_dir, data['fname']) + self.apilog_ext
            plt = check_platform(_bin)
            if "32bit" == plt:
                command_line = self.get_commandline("x86", path, log_path)
            elif "64bit" == plt:
                command_line = self.get_commandline("x64", path, log_path)
            else:
                self.send_json_wrapper({
                    {
                        "ip": self.sock.getsockname()[0],
                        "_timestamp": time(),
                        "action": action_id,
                        "success": False,
                        "target": data['fname'],
                        "err": "unknown platform to launch"
                    }
                })
                return -1
            
            """
            launch xLogger
            """
            proc = subprocess.Popen(command_line)
            try:
                proc.wait(timeout=10.0)
            except subprocess.TimeoutExpired as te:
                proc.terminate()
                self.logger.debug("subprocess killed with time exceeded (pid : %d)" % proc.pid)

            self.send_json_wrapper(
                {
                    "ip": self.sock.getsockname()[0],
                    "_timestamp": time(),
                    "action": action_id,
                    "success": True,
                    "target": data['fname']
                }
            )
        
        elif action_id == Agent.ActionID.GET_RESULT:
            # prasing execution result
            log_path = os.path.join(self.log_dir, data['fname']) + self.apilog_ext
            try:
                apis = parse_xlogger_result(log_path)
            except FileNotFoundError as fne:
                self.logger.error("Api log file is not exist (%s)" % log_path)
                self.send_json_wrapper(
                    {
                        "ip": self.sock.getsockname()[0],
                        "_timestamp": time(),
                        "action": action_id,
                        "success": False,
                        "target": data['fname'],
                        "err": ("api log file is not exist (%s)" % log_path)
                    }
                )
                
                return -1

            self.send_json_wrapper(
                {
                    "ip": self.sock.getsockname()[0],
                    "_timestamp": time(),
                    "action": action_id,
                    "success": True,
                    "target": data['fname'],
                    "data": apis['apis']
                }
            )
        
        elif action_id == Agent.ActionID.HALT:
            try:
                os.remove(self.apilog)
            except FileNotFoundError as fne:
                pass
            self.send_json_wrapper(
                {
                    "ip": self.sock.getsockname()[0],
                    "_timestamp": time(),
                    "action": action_id,
                    "success": True
                }
            )
            exit(-1)

        elif action_id == Agent.ActionID.GET_FILES_LIST:
            try:
                files = os.listdir(self.default_folder)
            except FileNotFoundError as fne:
                self.logger.critical("Share directory %s not exist" % self.default_folder)
                raise FileNotFoundError(fne)
            data = []
            for file in files:
                full_p = os.path.join(self.default_folder, file)
                meta = get_file_meta(full_p)
                meta['fname'] = file
                data.append(meta)
            self.send_json_wrapper(
                {
                    "ip": self.sock.getsockname()[0],
                    "_timestamp": time(),
                    "action": action_id,
                    "success": True,
                    "data": data
                }
            )

        elif action_id == Agent.ActionID.EXTRACT_FILE:
            targ = data['fname']
            data_port = data['port']
            _bin = b''
            file_exist = False
            try:
                files = os.listdir(self.default_folder)
            except FileNotFoundError as fne:
                self.logger.critical("Share directory %s not exist" % self.default_folder)
                raise FileNotFoundError(fne)
            if targ not in files:
                # maybe full path
                if os.path.exists(targ):
                    file_exist = True
            else:
                targ = os.path.join(self.default_folder, targ)
                file_exist = True

            if not file_exist:
                self.send_json_wrapper(
                    {
                        "ip": self.sock.getsockname()[0],
                        "_timestamp": time(),
                        "action": action_id,
                        "success": False,
                        "err": 'requested file does not exist'
                    }
                )
                return -1
            else:
                self.send_json_wrapper(
                    {
                        "ip": self.sock.getsockname()[0],
                        "_timestamp": time(),
                        "action": action_id,
                        "success": True
                    }
                )
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_sock:
                    try:
                        data_sock.connect((self.server_ip, data_port))
                        with open(targ, 'rb') as f:
                            data_sock.sendfile(f)
                        data_sock.close()
                    except Exception as e:
                        self.logger.error("send file error with %s" % e)

        self.logger.debug("action_handler handled action %d successfully!" % action_id)
        return 0

    def get_commandline(self, platform, target, log_path):
        # xLogger.exe --apis-dir "..\\WinApi" --headers-dir "..\\WinAPI\\headers"  -c C:\\Windows\\System32\\notepad.exe -l "..\..\log.txt"
        return [
            os.path.join(self.launch_path, "bin", "xLogger", platform, "xLogger.exe"),
            "--apis-dir", os.path.join(self.launch_path, "bin", "xLogger", "WinApi"),
            "--headers-dir", os.path.join(self.launch_path, "bin", "xLogger","WinApi", "headers"),
            "-c", target,
            "-l", log_path,
            "--hide-debugger"
        ]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog='API Logger Agent',
        description=dedent('''
        Agent of API Logger Sandbox
        > Based on xLogger "https://github.com/d35ha/xLogger"
        '''))
    
    parser.add_argument('--dest', type=str, default='localhost', help='API Logger server IP')
    parser.add_argument('--port', type=int, default=7011, help='API Logger server port')

    args = parser.parse_args()
    agent = Agent(args.dest, args.port)
    agent.launch()

    pass