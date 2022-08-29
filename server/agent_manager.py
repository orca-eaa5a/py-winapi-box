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

    def __init__(self, server_ip='127.0.0.1', port=7011) -> None:
        self.server_ip = server_ip
        self.port = port
        self.connection = None
        self.data_queue = {
            AgentManager.ActionID.CREATE_FILE: [],
            AgentManager.ActionID.CREATE_PROCESS: [],
            AgentManager.ActionID.GET_RESULT: [],
            AgentManager.ActionID.HALT: [],
            AgentManager.ActionID.GET_FILES_LIST: [],
        }
        self.job_evt = threading.Event()
        self.logger = AgentLogger().logger
        self.ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
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

    def send_command(self, action, data):
        if self.job_evt.isSet():
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
            else:
                self.logger.error("Unknown command")
                return -1

            self.connection.send(json.dumps(body).encode("utf-8"))
            if action == AgentManager.ActionID.CREATE_FILE:
                self.connection.send(data['raw'])
            self.job_evt.wait()
            self.job_evt.clear()
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
                        self.data_queue[data['action']].append(
                            data
                        )
                        self.job_evt.set()
                except ConnectionResetError as cre:
                    self.logger.error("Client %s connection closed" % self.connection.getsockname()[0])
                    break
                except Exception as e:
                    self.close_server(e)
                    break