import os
from flask import Flask, render_template, request, json
from flask_cors import CORS, cross_origin
from manager.agent_manager import AgentManager
from manager.vbox.vbox_manager import VBoxManager
from manager.vbox.vbox_exceptions import *
# from multiprocessing import Process
from threading import Thread

template_dir = os.path.join(__file__, os.pardir, "public")
static_dir = os.path.join(__file__, os.pardir, "public")
app = Flask(__name__, 
    static_folder=static_dir,
    template_folder=template_dir
)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route('/')
def home():
    return 'Hello, World!'

@app.route('/board', methods=['GET'])
def go_board():
    return render_template("board.html")

@app.route('/main', methods=['GET'])
def go_main():
    return render_template("main.html")

@app.route('/sandbox', methods=['GET'])
def go_sandbox():
    return render_template("sandbox.html")

@app.route('/upload', methods=['POST'])
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
    data = agent_man.action_queue[agent_man.ActionID.CREATE_FILE]['data'].pop(0)
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
    data = agent_man.action_queue[agent_man.ActionID.CREATE_PROCESS]['data'].pop(0)
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/log/<program>')
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
    data = agent_man.action_queue[agent_man.ActionID.GET_RESULT]['data'].pop(0)
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    # data = agent_man.action_queue[agent_man.ActionID.GET_RESULT]['data'].pop(0)
    return response

@app.route('/files')
def get_files():
    agent_man = app.config['agent-man']
    r = agent_man.send_command(
        action=agent_man.ActionID.GET_FILES_LIST,
        data={}
        )
    if r == -2:
        return '507 Another job is running'
    elif r == -1:
        return '400 Bad request'
    data = agent_man.action_queue[agent_man.ActionID.GET_FILES_LIST]['data'].pop(0)
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )
    return response

@app.route('/extract')
def extract_files():
    agent_man = app.config['agent-man']
    r = agent_man.send_command(
        action=agent_man.ActionID.EXTRACT_FILE,
        data={'fname': "createprocess.exe"}
        )

    if r == -2:
        return '507 Another job is running'
    elif r == -1:
        return '400 Bad request'

    data = agent_man.action_queue[agent_man.ActionID.EXTRACT_FILE]['data'].pop(0)
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
    data = agent_man.action_queue[agent_man.ActionID.HALT]['data'].pop(0)
    return data

@app.route('/vbox/list', methods=['GET'])
def get_vbox_list():
    vbox_man = app.config['vbox-man']
    data = {}
    out = vbox_man.get_vbox_list()
    data['vbox'] = out
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )

    return response

@app.route('/vbox/status/<vbox_name>', methods=['GET'])
def get_vbox_status(vbox_name):
    vbox_man = app.config['vbox-man']
    data = {}
    out = vbox_man.get_vbox_status(vbox_name)
    if not out:
        data['success'] = False
    else:
        data = out
        data['success'] = True

    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )

    return response

@app.route('/vbox/snapshots/<vbox_name>')
def get_snapshot_list(vbox_name):
    vbox_man = app.config['vbox-man']
    data = {}
    out = vbox_man.get_snapshot_lsit(vbox_name)
    data['vbox'] = vbox_name
    data['snapshots'] = out
    response = app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )

    return response

@app.route('/vbox/run/<vbox_name>', methods=['GET', 'POST'])
def run_vbox(vbox_name):
    vbox_man = app.config['vbox-man']
    if request.method == 'GET':
        out = {}
        out['vbox'] = vbox_name
        out['running'] = False
        if vbox_man.check_vbox_running(vbox_name):
            out['running'] = True
        
    if request.method == 'POST':
        # launch vbox
        out = {}
        out['vbox'] = vbox_name
        out['success'] = False
        try:
            if vbox_man.launch_vbox(vbox_name):
                out['success'] = True
        except MachineAlreadyRunning as mar:
            out['err'] = "already running"
        except MachineNotExist as mne:
            out['err'] = "target machine not exist"

    response = app.response_class(
        response=json.dumps(out),
        status=200,
        mimetype='application/json'
    )

    return response

@app.route('/vbox/resume/<vbox_name>', methods=['GET', 'POST'])
def resume_vbox(vbox_name):
    vbox_man = app.config['vbox-man']
        
    if request.method == 'POST':
        # pase vbox
        out = {}
        out['vbox'] = vbox_name
        out['success'] = False
        try:
            if vbox_man.resume_vbox(vbox_name):
                out['success'] = True
        except (MachineAlreadyRunning, ResumeMachineFailed) as mar:
            out['err'] = "already running"
        except MachineNotExist as mne:
            out['err'] = "target machine not exist"

    response = app.response_class(
        response=json.dumps(out),
        status=200,
        mimetype='application/json'
    )

    return response

@app.route('/vbox/pause/<vbox_name>', methods=['GET', 'POST'])
def pause_vbox(vbox_name):
    vbox_man = app.config['vbox-man']
        
    if request.method == 'POST':
        # pase vbox
        out = {}
        out['vbox'] = vbox_name
        out['success'] = False
        try:
            if vbox_man.pause_vbox(vbox_name):
                out['success'] = True
        except MachineAlreadyShutdown as mar:
            out['err'] = "already running"
        except MachineNotExist as mne:
            out['err'] = "target machine not exist"

    response = app.response_class(
        response=json.dumps(out),
        status=200,
        mimetype='application/json'
    )

    return response

@app.route('/vbox/halt/<vbox_name>', methods=['GET', 'POST'])
def halt_vbox(vbox_name):
    vbox_man = app.config['vbox-man']
        
    if request.method == 'POST':
        # pase vbox
        out = {}
        out['vbox'] = vbox_name
        out['success'] = False
        try:
            if vbox_man.shutdown_vbox(vbox_name):
                out['success'] = True
        except MachineAlreadyRunning as mar:
            out['err'] = "already running"
        except MachineNotExist as mne:
            out['err'] = "target machine not exist"

    response = app.response_class(
        response=json.dumps(out),
        status=200,
        mimetype='application/json'
    )

    return response

if __name__ == '__main__':
    agent_man = AgentManager()
    vbox_man = VBoxManager()
    app.config['agent-man'] = agent_man
    app.config['vbox-man'] = vbox_man

    # Process(target=agent_man.runserver, args=())
    listener = Thread(target=agent_man.runserver, args=())
    listener.start()
    # app.debug = True
    app.run()