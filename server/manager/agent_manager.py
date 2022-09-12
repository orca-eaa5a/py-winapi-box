import os
import json
import socket
import threading
from utils.agent_logger import AgentLogger

class AgentManager(object):
    class ActionID:
        INIT = 0
        CREATE_FILE=1
        CREATE_PROCESS=2
        GET_RESULT=3
        HALT=4
        GET_FILES_LIST=5
        EXTRACT_FILE=6

    def __init__(self, server_ip='0.0.0.0', port=7011) -> None:
        self.action_queue = {
            AgentManager.ActionID.CREATE_FILE: {
                'name': 'CREATE_FILE',
                'data': []
            },
            AgentManager.ActionID.CREATE_PROCESS: {
                'name': 'CREATE_PROCESS',
                'data': []
            },
            AgentManager.ActionID.GET_RESULT: {
                'name': 'GET_RESULT',
                'data': []
            },
            AgentManager.ActionID.HALT: {
                'name': 'HALT',
                'data': []
            },
            AgentManager.ActionID.GET_FILES_LIST: {
                'name': 'GET_FILES_LIST',
                'data': []
            },
            AgentManager.ActionID.EXTRACT_FILE:{
                'name': 'EXTRACT_FILE',
                'data': []
            }
        }
        
        self.events = {}
        self.init_sync_event()
        self.server_ip = server_ip
        self.port = port
        self.connection = None
        self.logger = AgentLogger().logger
        self.ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.agent_root = os.path.abspath(os.path.join(__file__, os.pardir))
        self.setup_server_sock()
        pass

    def setup_server_sock(self):
        self.ssock.bind((self.server_ip, self.port))
        self.ssock.listen(1)

    def close_server(self, *args):
        if not args:
            self.logger.info("Server closed")
        else:
            self.logger.error("Server closed with error %s" % args)
        self.ssock.close()

    def close_client(self):
        self.logger.info("Client %s connection closed" % self.connection.getsockname[0])
        self.connection.close()

    def recv_json_wrapper(self):
        EOM = b'orca.eaa5a'
        EOM_OFFSET = int(-1*len(EOM))
        try:
            data = b''
            while True:
                data += self.connection.recv(1024)
                if not data:
                    break
                if data[EOM_OFFSET:] == EOM:
                    data = data[:EOM_OFFSET]
                    break
            return json.loads(data.decode("utf-8"))
        except json.JSONDecodeError:
            self.logger.error("invalid json format %s" % str(data))
        except Exception as e:
            self.logger.error("recv failed with error %s" % e)
        return None

    def init_sync_event(self):
        for key in self.action_queue:
            self.events[self.action_queue[key]['name']] = threading.Event()
    
    def is_event_availiable(self, action_id):
        attr = self.action_queue[action_id]['name']
        evt = self.events[attr]
        if evt.is_set():
            # another job is running
            # can't wait
            return False
        return True

    def set_sync_event(self, action_id):
        attr = self.action_queue[action_id]['name']
        evt = self.events[attr]
        evt.set()
    
    def wait_sync_event(self, action_id):
        attr = self.action_queue[action_id]['name']
        evt = self.events[attr]
        evt.wait()
        evt.clear()
    
    def file_recv_socket(self, fname, port):
        _bin = b''
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as data_sock:
            data_sock.bind(('0.0.0.0', port))
            data_sock.listen(1)
            data_conn, _addr = data_sock.accept()
            while True:
                _bin = data_conn.recv(1024)
                if not _bin:
                    data_conn.close()
                    break
        path = os.path.join(self.agent_root, "extract", fname)
        with open(path, 'wb') as f:
            f.write(_bin)
        

    def send_command(self, action, data):
        if not self.is_event_availiable(action_id=action):
            return -2
        try:
            body = {'data': {}}
            body['act_id'] = action
            if action == AgentManager.ActionID.CREATE_FILE:
                body['data']['fname'] = data['fname']
                body['data']['file_sz'] = data['file_sz']

            elif action == AgentManager.ActionID.CREATE_PROCESS:
                body['data']['fname'] = data['fname']
                pass
            
            elif action == AgentManager.ActionID.GET_RESULT:
                body['data']['fname'] = data['fname']
                pass

            elif action == AgentManager.ActionID.HALT:
                pass
            elif action == AgentManager.ActionID.GET_FILES_LIST:
                pass

            elif action == AgentManager.ActionID.EXTRACT_FILE:
                file_recv_port = 59912
                body['data']['fname'] = data['fname']
                body['data']['port'] = file_recv_port
                threading.Thread(target=self.file_recv_socket, args=(data['fname'], file_recv_port)).start()
                
            else:
                self.logger.error("Unknown command")
                return -1

            self.connection.send(json.dumps(body).encode("utf-8"))
            if action == AgentManager.ActionID.CREATE_FILE:
                self.connection.send(data['raw'])

            self.wait_sync_event(action_id=action)
            return 0

        except ConnectionResetError as cre:
            self.logger.error("Client %s connection already closed" % self.connection.getsockname()[0])
        except Exception as e:
            self.logger.error("Unknown exception in send() %s" % e)
        
        return -1

    def runserver(self):
        while True:
            self.connection, addr = self.ssock.accept()
            while True:
                try:
                    data = self.recv_json_wrapper()
                    if not data:
                        self.logger.info("Client %s connection closed" % self.connection.getsockname()[0])
                        self.connection.close()
                        break
                    if data['action'] == AgentManager.ActionID.INIT:
                        self.logger.info("Client %s connected" % self.connection.getsockname()[0])
                    else:
                        self.action_queue[data['action']]['data'].append(data)
                        self.set_sync_event(action_id=data['action'])
                except ConnectionResetError as cre:
                    self.logger.error("Client %s connection closed" % self.connection.getsockname()[0])
                    break
                except Exception as e:
                    self.close_server(e)
                    break