import os
import platform
import subprocess
from tkinter.messagebox import NO
class VBoxManager(object):
    def __init__(self, vbox_name) -> None:
        self.vbox_name = vbox_name
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
        raise Exception("Can't find Virtualbox installation path: Did you set %PATH% env?")

    def call_vbox_manager(self, options):
        cmdline = ["vboxmanage"] + options
        p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = p.communicate()
        if out:
            out = out.decode("utf-8")
            if self.platform == "Windows":
                out = out.replace("\r\n", "\n")
                if out[-1] == "\n":
                    out = out[:-1]
        
        return (out, err)

    def check_vbox_exist(self):
        out, err = self.call_vbox_manager(options=["list", "vms"])
        if not out:
            raise Exception("Fail to call vboxmanage with error %s" % err)
        vm_list = out.split(r"\n")
        for vm in vm_list:
            if self.vbox_name in vm:
                return True
        return False

    def check_vbox_running(self):
        out, err = self.call_vbox_manager(options=["list", "runningvms"])
        if not out and not err:
            # no response : no vbox running
            return False
        if not out:
            raise Exception("Fail to call vboxmanage with error %s" % err)
        vm_list = out.split(r"\n")
        for vm in vm_list:
            if self.vbox_name in vm:
                return True
        return False

    def launch_vbox(self):
        out, err = self.call_vbox_manager(options=["startvm", self.vbox_name])
        if not out:
            raise Exception("Fail to call vboxmanage with error %s" % err)
        
        return out
    
    def shutdown_vbox(self):
        out, err = self.call_vbox_manager(options=["controlvm", self.vbox_name, "poweroff"])
        e = err.decode("utf-8")
        if self.platform == "Windows":
            e = e.replace("\r\n", "\n")
            if e[-1] == "\n":
                e = e[:-1]
        if not "100%" in e:
            raise Exception("Fail to call vboxmanage with error %s" % err)

        return True

    def pause_vbox(self):
        out, err = self.call_vbox_manager(options=["controlvm", self.vbox_name, "pause"])
        if not out:
            raise Exception("Fail to call vboxmanage with error %s" % err)

        return out

    def resume_vbox(self):
        out, err = self.call_vbox_manager(options=["controlvm", self.vbox_name, "resume"])
        if not out:
            raise Exception("Fail to call vboxmanage with error %s" % err)

        return out

    def check_snapshot_exist(self, snapshot_name=None):
        out, err = self.call_vbox_manager(options=["snapshot", self.vbox_name, "list"])
        if not out:
            raise Exception("Fail to call vboxmanage with error %s" % err)

        if out == "This machine does not have any snapshots":
            return False
        else:
            if not snapshot_name and \
                self.default_snapshot in out:
                return True
        return False

    def takesnapshot_vbox(self, snapsnot_name=None):
        if not snapsnot_name:
            snapsnot_name = self.default_snapshot
        out, err = self.call_vbox_manager(options=["snapshot", self.vbox_name, "take", snapsnot_name])
        e = err.decode("utf-8")
        if self.platform == "Windows":
            e = e.replace("\r\n", "\n")
            if e[-1] == "\n":
                e = e[:-1]
        if not "100%" in e:
            raise Exception("Fail to call vboxmanage with error %s" % err)
        
        return True

    def revertsnapsnot_vbox(self, snapsnot_name=None):
        if not snapsnot_name:
            snapsnot_name = self.default_snapshot
        if self.check_vbox_running():
            self.shutdown_vbox()

        out, err = self.call_vbox_manager(options=["snapshot", self.vbox_name, "restore", snapsnot_name])
        if "Restoring snapshot '%s'" % snapsnot_name in out:
            self.launch_vbox()
            return True
        else:
            raise Exception("Fail to call vboxmanage with error %s" % err)
        pass
    

if __name__ == '__main__':
    vbox_manager = VBoxManager('vbox-win7')
    # out = vbox_manager.check_vbox_exist()
    # if not out:
    #     print(vbox_manager.vbox_name + " dose not exist")
    # print(vbox_manager.vbox_name + " exist")
    # vbox_manager.launch_vbox()
    vbox_manager.shutdown_vbox()
    # if not vbox_manager.check_snapshot_exist():
    #     vbox_manager.takesnapshot_vbox()
    # vbox_manager.revertsnapsnot_vbox()
    pass
