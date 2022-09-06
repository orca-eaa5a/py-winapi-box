import os
import platform
import subprocess
import manager.vbox.result_parser as result_parser
from manager.vbox.vbox_exceptions import *

class VBoxManager(object):
    def __init__(self) -> None:
        self.vbox_path = self.get_vbox_installation_path()
        self.platform = platform.system()
        self.shell = ""
        self.default_snapshot = "snap1"
        if self.platform == "Windows":
            self.shell = "cmd.exe"
        elif self.platform == "Darwin":
            # OSX
            self.shell = os.environ["SHELL"]
        else:
            # Linux
            self.shell = os.environ["SHELL"]

    def get_vbox_installation_path(self):
        env = os.getenv("PATH").split(";")
        for e in env:
            if 'virtualbox' in e.lower():
                return e
        raise VBoxConfigurationError("Can't find Virtualbox installation path: Did you set %PATH% env?")

    def call_vbox_manager(self, options):
        cmdline = ["vboxmanage"] + options
        p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        # In trivial case, 
        # message is just transfered at err even if operation is succssed.
        # So, return either out & err

        if out:
            out = out.decode("utf-8")
            if self.platform == "Windows":
                out = out.replace("\r\n", "\n")
                if out[-1] == "\n":
                    out = out[:-1]
        
        return (out, err)

    def get_vbox_list(self):
        out, err = self.call_vbox_manager(options=["list", "vms"])
        if not out:
            raise UnknownVBoxException(err)
            
        result = result_parser.parse_vmlist(out)            
        return result

    def get_vbox_status(self, vbox_name):
        out, err = self.call_vbox_manager(options=["showvminfo", vbox_name])
        if not out:
            if b'Could not find a registered machine' in err:
                raise MachineNotExist(vbox_name)
            else:
                raise UnknownVBoxException(err)
        vm_info = result_parser.parse_vminfo(out)
        return vm_info
        

    def check_vbox_exist(self, vbox_name):
        out, err = self.call_vbox_manager(options=["list", "vms"])
        if not out:
            raise UnknownVBoxException(err)

        vm_list = out.split("\n")
        for vm in vm_list:
            if vbox_name in vm:
                return True
        return False

    def check_vbox_running(self, vbox_name):
        out, err = self.call_vbox_manager(options=["list", "runningvms"])
        if not out and not err:
            # no response : there is no running vbox.
            return False
        if not out:
            raise UnknownVBoxException(err)
            
        vm_list = out.split("\n")
        for vm in vm_list:
            if vbox_name in vm:
                return True

        return False

    def launch_vbox(self, vbox_name):
        out, err = self.call_vbox_manager(options=["startvm", vbox_name])
        if not out:
            if b'Could not find a registered machine' in err:
                raise MachineNotExist(vbox_name)
            elif b'already locked by a session' in err:
                raise MachineAlreadyRunning(vbox_name)
            raise UnknownVBoxException(err)
        
        if "successfully started" in out:
            return True
        
        return False
    
    def shutdown_vbox(self, vbox_name):
        out, err = self.call_vbox_manager(options=["controlvm", vbox_name, "poweroff"])
        e = err.decode("utf-8")
        if self.platform == "Windows":
            e = e.replace("\r\n", "\n")
            if e[-1] == "\n":
                e = e[:-1]

        if not "100%" in e and "error" in e:
            if b'Could not find a registered machine' in err:
                raise MachineNotExist(vbox_name)
            elif b'not currently running' in err:
                raise MachineIsNotRunning(vbox_name)
            else:
                raise UnknownVBoxException(err)
        
        return True

    def pause_vbox(self, vbox_name):
        out, err = self.call_vbox_manager(options=["controlvm", vbox_name, "pause"])
        e = err.decode("utf-8")        
        if self.platform == "Windows":
            e = e.replace("\r\n", "\n")
            if e[-1] == "\n":
                e = e[:-1]

        if not "100%" in e and "error" in e:
            if b'Could not find a registered machine' in err:
                raise MachineNotExist(vbox_name)
            elif b'not currently running' in err:
                raise MachineIsNotRunning(vbox_name)
            else:
                raise UnknownVBoxException(err)

        return True

    def resume_vbox(self, vbox_name):
        out, err = self.call_vbox_manager(options=["controlvm", vbox_name, "resume"])
        e = err.decode("utf-8")        
        if self.platform == "Windows":
            e = e.replace("\r\n", "\n")
            if e[-1] == "\n":
                e = e[:-1]

        if not "100%" in e and "error" in e:
            if b'Could not find a registered machine' in err:
                raise MachineNotExist(vbox_name)
            elif b'not currently running' in err:
                raise MachineIsNotRunning(vbox_name)
            elif b'Cannot resume the machine as it is not paused' in err:
                raise ResumeMachineFailed(err)
            else:
                raise UnknownVBoxException(err)

        return True

    def get_snapshot_lsit(self, vbox_name):
        out, err = self.call_vbox_manager(options=["snapshot", vbox_name, "list"])

        if not out:
            raise UnknownVBoxException(err)

        if out == "This machine does not have any snapshots":
            return [] # empty list

        return result_parser.parse_snapshotlist(out)

    def check_snapshot_exist(self, vbox_name, snapshot_name=None):
        snapshots = self.get_snapshot_lsit(vbox_name)
        if not snapshots:
            return False

        if snapshot_name in snapshots:
            return True
        
        return False

    def takesnapshot_vbox(self, vbox_name, snapsnot_name=None):
        if not snapsnot_name:
            snapsnot_name = self.default_snapshot

        if self.check_snapshot_exist(vbox_name, snapsnot_name):
            raise DuplicateShapsnot(snapsnot_name)

        out, err = self.call_vbox_manager(options=["snapshot", vbox_name, "take", snapsnot_name])
        e = err.decode("utf-8")
        if self.platform == "Windows":
            e = e.replace("\r\n", "\n")
            if e[-1] == "\n":
                e = e[:-1]

        if not "100%" in e:
            raise UnknownVBoxException(err)
        
        if 'Snapshot taken' in out:
            return True
        raise UnknownVBoxException(err)

    def revertsnapsnot_vbox(self, vbox_name, snapsnot_name=None):
        if not snapsnot_name:
            snapsnot_name = self.default_snapshot
        
        if self.check_vbox_running():
            self.shutdown_vbox()

        if not self.check_snapshot_exist():
            RevertMachineFailed(b'No target Snapshot')

        out, err = self.call_vbox_manager(options=["snapshot", vbox_name, "restore", snapsnot_name])
        if "Restoring snapshot '%s'" % snapsnot_name in out:
            self.launch_vbox()
            return True
        
        raise UnknownVBoxException(err)
        
    

if __name__ == '__main__':
    vbox_manager = VBoxManager()
    # out = vbox_manager.check_vbox_exist()
    # if not out:
    #     print(vbox_manager.vbox_name + " dose not exist")
    # print(vbox_manager.vbox_name + " exist")
    vbox_manager.launch_vbox('vbox-win7')
    # vbox_manager.shutdown_vbox()
    # if not vbox_manager.check_snapshot_exist():
    # vbox_manager.takesnapshot_vbox('vbox-win7', 'test2')
    # vbox_manager.revertsnapsnot_vbox()
    pass
