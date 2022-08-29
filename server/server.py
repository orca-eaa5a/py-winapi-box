from io import BytesIO
import os
from flask import Flask, render_template, request
from agent_manager import AgentManager
# from multiprocessing import Process
from threading import Thread

template_dir = os.path.join(__file__, os.pardir, "public")

app = Flask(__name__, template_folder=template_dir)
@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/file', methods=['GET'])
def file_select():
    return render_template("upload.html")

@app.route('/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        file = request.files['target']
        _bin = file.read()

    agent_man = app.config['agent-man']
    r = agent_man.send_command(
            action=agent_man.ActionID.CREATE_FILE,
            data={
                'fname': file.filename,
                'file_sz': len(_bin),
                'raw': _bin
            }
        )
    if r == -2:
        return '507 Another job is running'
    elif r == -1:
        return '400 Bad request'
    data = agent_man.data_queue[agent_man.ActionID.CREATE_FILE].pop(0)
    return data

@app.route('/exec/<program>')
def execute(program):
    if not program:
        return '403'
    agent_man = app.config['agent-man']
    r = agent_man.send_command(
        action=agent_man.ActionID.CREATE_PROCESS,
        data={'fname': program}
        )
    if r == -2:
        return '507 Another job is running'
    elif r == -1:
        return '400 Bad request'
    data = agent_man.data_queue[agent_man.ActionID.CREATE_PROCESS].pop(0)
    return data

@app.route('/get-log/<program>')
def get_winapi(program):
    agent_man = app.config['agent-man']
    r = agent_man.send_command(
        action=agent_man.ActionID.GET_RESULT,
        data={'fname': program}
        )

    if r == -2:
        return '507 Another job is running'
    elif r == -1:
        return '400 Bad request'
    data = agent_man.data_queue[agent_man.ActionID.GET_RESULT].pop(0)
    return data

@app.route('/halt')
def halt_agent():
    agent_man = app.config['agent-man']
    r = agent_man.send_command(
        action=agent_man.ActionID.HALT,
        data=""
        )
    
    if r == -2:
        return '507 Another job is running'
    elif r == -1:
        return '400 Bad request'
    data = agent_man.data_queue[agent_man.ActionID.HALT].pop(0)
    return data

if __name__ == '__main__':
    agent_man = AgentManager()
    app.config['agent-man'] = agent_man
    # Process(target=agent_man.runserver, args=())
    listener = Thread(target=agent_man.runserver, args=())
    listener.start()
    app.run()