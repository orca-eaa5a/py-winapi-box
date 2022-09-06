class VBoxConfigurationError(Exception):
    def __init__(self, errmsg:str) -> None:
        self.errmsg = errmsg
        pass

    def __str__(self) -> str:
        return self.errmsg

class MachineIsNotRunning(Exception):
    def __init__(self, machine_name) -> None:
        self.machine_name = machine_name
        pass

    def __str__(self) -> str:
        return "Target machine [%s] is not running" % self.machine_name    

class MachineAlreadyRunning(Exception):
    def __init__(self, machine_name) -> None:
        self.machine_name = machine_name
        pass

    def __str__(self) -> str:
        return "Target machine [%s] is already running" % self.machine_name

class MachineAlreadyShutdown(Exception):
    def __init__(self, machine_name) -> None:
        self.machine_name = machine_name
        pass

    def __str__(self) -> str:
        return "Target machine [%s] is already shutdowned" % self.machine_name    

class MachineNotExist(Exception):
    def __init__(self, machine_name) -> None:
        self.machine_name = machine_name
        pass

    def __str__(self) -> str:
        return "Could not find a registered machine named [%s]" % self.machine_name

class DuplicateShapsnot(Exception):
    def __init__(self, snapshot_name) -> None:
        self.snapshot_name = snapshot_name
        pass

    def __str__(self) -> str:
        return "Could not take snapshot : Snapshot name [%s] is duplicated" % self.snapshot_name

class RevertMachineFailed(Exception):
    def __init__(self, errmsg:bytes) -> None:
        self.errmsg = errmsg.decode("utf-8").replace("\r\n", "\n")
        pass

    def __str__(self) -> str:
        return "Revert Machine Failed with error %s" % self.errmsg

class ResumeMachineFailed(Exception):
    def __init__(self, errmsg) -> None:
        self.errmsg = errmsg
        pass

    def __str__(self) -> str:
        return "Resume machine Failed with error %s" % self.errmsg

class UnknownVBoxException(Exception):
    def __init__(self, errmsg) -> None:
        self.errmsg = errmsg.decode("utf-8").replace("\r\n", "\n")
    
    def __str__(self) -> str:
        return "Undefined VBox Exception Occured with error %s" % self.errmsg