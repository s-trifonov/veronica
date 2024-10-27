import sys, abc

from tools.utils import raiseRuntimeError
from tools.runtime import RT_Guard

#================================
class StepCommand:
    def __init__(self):
        self.mDone        = False
        self.mCtrlState   = None
        self.mpatron_agent = None

    def _setpatron_agent(self, patron_agent):
        assert self.mpatron_agent is None
        self.mpatron_agent = patron_agent
        self.mpatron_agent._regOn(self)

    @abc.abstractmethod
    def getCmdName(self):
        assert False

    def getWeight(self):
        return 1

    @abc.abstractmethod
    def doIt(self, master):
        assert not self.mDone
        self.mDone = True

    @abc.abstractmethod
    def undoIt(self, master):
        assert self.mDone
        self.mDone = False

    def __len__(self):
        return 1

    def getPatronage(self):
        if self.mpatron_agent is not None:
            return self.mpatron_agent.getPatronage()
        return None

    def deactivate(self):
        if self.mpatron_agent:
            self.mpatron_agent._regOff(self)
        return self

    def isEmpty(self):
        return self.getWeight() <= 0

    def getDescr(self):
        assert False

#===============================================
def _deactivateStack(the_stack):
    ret = []
    while len(the_stack) > 0:
        step_no, command = the_stack[0]
        del the_stack[0]
        command = command.deactivate()
        if command:
            ret.append((step_no, command))
    return ret

def _delOneFromStack(the_stack):
    step_no, command = the_stack[0]
    command.deactivate()
    del the_stack[0]

def _deactivateOneFromStack(the_stack, idx):
    step_no, command = the_stack[idx]
    del the_stack[idx]
    command = command.deactivate()
    if command:
        the_stack.insert(idx, (step_no, command))

#===============================================
class SeqStepCommand(StepCommand):
    def __init__(self, descr = None, commands = None):
        StepCommand.__init__(self)
        self.mDescr = descr
        if commands:
            self.mSeq = [command for command in commands]
        else:
            self.mSeq = []

    def addOne(self, command):
        self.mSeq.append(command)

    def insertOne(self, command):
        self.mSeq.insert(0, command)

    def setDescr(self, descr):
        self.mDescr = descr

    def isEmpty(self):
        return any(command.isEmpty() for command in self.mSeq)

    def __len__(self):
        return len(self.mSeq)

    def getDescr(self):
        return self.mDescr

    def getLast(self):
        return self.mSeq[-1]

    def getWeight(self):
        if len(self.mSeq) == 0:
            return 0
        return sum(command.getWeight() for command in self.mSeq)

    def purify(self):
        if len(self.mSeq) == 0:
            return None
        if len(self.mSeq) == 1:
            return self.mSeq[0]
        return self

    def getCmdName(self):
        return "<sequence of %d>" % len(self.mSeq)

    def onStep(self, master):
        pass

    def doIt(self, master):
        StepCommand.doIt(self, master)
        for idx in range(len(self.mSeq)):
            self.mSeq[idx].doIt(master)
            self.onStep(master)

    def undoIt(self, master):
        for idx in range(len(self.mSeq)-1, -1, -1):
            self.mSeq[idx].undoIt(master)
            self.onStep(master)
        StepCommand.undoIt(self, master)

#================================
def joinCommands(cmd1, cmd2):
    if cmd1 is None:
        return cmd2
    if cmd2 is None:
        return cmd1
    if isinstance(cmd1, SeqStepCommand):
        if isinstance(cmd2, SeqStepCommand):
            cmd1.mSeq += cmd2.mSeq
            return cmd1
        cmd1.mSeq.append(cmd2)
        return cmd1
    if isinstance(cmd2, SeqStepCommand):
        cmd2.mSeq.insert(0, cmd1)
        return cmd2
    ret = SeqStepCommand()
    ret.addOne(cmd1)
    ret.addOne(cmd2)
    return ret

#================================
# Patronage is a singleton, that only knows who is master or slave
#================================
class PatronageCommandPack:
    def __init__(self, slave_controller, base_command, master_obj):
        self.mSlaveController = slave_controller
        self.mBaseCommand     = base_command
        self.mMasterObj       = master_obj

    def doEval(self, master):
        return master.evalWithPatronage(self.mSlaveController,
            self.mBaseCommand, self.mMasterObj)

#================================
class StepController:
    def __init__(self,
            max_undo_count  = 300,
            min_undo_count  = 10,
            max_undo_weight = 500):

        self.mMaxUndoCount  = max_undo_count
        self.mMinUndoCount  = min_undo_count
        self.mMaxUndoWeight = max_undo_weight

        self.mIncStepCount  = 0
        self.mCurrentStep   = 0
        self.mSavedStep     = 0
        self.mChangeStack   = []
        self.mRedoStack     = []

        self.mInOperation   = 0

        self.mPatronage     = None

    def noSavedVersion(self):
        self.mSavedStep = None

    def getCurStep(self):
        return self.mCurrentStep

    def getSavedStep(self):
        return self.mSavedStep

    def needsSave(self):
        return self.mCurrentStep != self.mSavedStep

    def onSaveStep(self):
        self.mSavedStep = self.mCurrentStep

    def canCancel(self):
        return (self.mSavedStep is not None
            and self.mCurrentStep != self.mSavedStep)

    def evalWithPatronage(self, slave_controller, command, master_obj):
        if self.mPatronage is not None:
            if self.mPatronage.mSlave is not slave_controller:
                self._setPatronage(None)
        else:
            StepPatronage(self, slave_controller)
        return self.mPatronage.evalCommand(command, master_obj)

    def _setPatronage(self, patronage):
        if self.mPatronage is patronage:
            return
        if self.mPatronage is not None:
            self.mChangeStack = _deactivateStack(self.mChangeStack)
            self.mRedoStack   = _deactivateStack(self.mRedoStack)
            self.mPatronage.deactivate()
        self.mPatronage = patronage

    def onCancel(self):
        self._setPatronage(None)
        self.mChangeStack   = []
        self.mRedoStack     = []
        self.mCurrentStep   = self.mSavedStep

    def forgetAll(self):
        self._setPatronage(None)
        self.mIncStepCount += 1
        self.mCurrentStep   = self.mSavedStep = self.mIncStepCount
        self.mChangeStack   = []
        self.mRedoStack     = []

    def _cleanup(self):
        while len(self.mChangeStack) >= self.mMaxUndoCount:
            _delOneFromStack(self.mChangeStack)

        while len(self.mChangeStack) > self.mMinUndoCount and (
            sum(command.getWeight() for step, command in self.mChangeStack)
                >= self.mMaxUndoWeight):
            _delOneFromStack(self.mChangeStack)

    def onOperationStart(self, command, eval_mode):
        self.pushOperation()
        return True

    def onOperationEnd(self, command, eval_mode):
        self.popOperation()

    def evalCommand(self, command, under_patronage = False):
        if isinstance(command, PatronageCommandPack):
            return command.doEval(self)

        if self.mInOperation > 0:
            raiseRuntimeError("OP in OP!!!")

        if not under_patronage and self.mPatronage is not None:
            return self.mPatronage._evalCommand(self, command)

        if not self.onOperationStart(command, 0):
            return False

        self.mChangeStack.append((self.mCurrentStep, command))
        self.mIncStepCount += 1
        self.mCurrentStep = self.mIncStepCount
        _deactivateStack(self.mRedoStack)
        self.mRedoStack = []
        assert not RT_Guard.isFree()
        try:
            command.doIt(self)
        finally:
            self._cleanup()
            self.onOperationEnd(command, 0)
        return True

    def canUndo(self):
        return len(self.mChangeStack) > 0

    def countUndo(self):
        return len(self.mChangeStack)

    def evalUndo(self, under_patronage = False):
        if not under_patronage and self.mPatronage:
            return self.mPatronage._evalUndo(self)

        prev_step, command = self.mChangeStack.pop()
        self.mRedoStack.append((self.mCurrentStep, command))
        assert (self.mCurrentStep > prev_step
            or (self.mCurrentStep == prev_step
            and isinstance(command, PatronnedMasterStepCommand)))
        assert not RT_Guard.isFree()

        if not self.onOperationStart(command, -1):
            return False

        try:
            self.mCurrentStep = prev_step
            command.undoIt(self)
        finally:
            self.onOperationEnd(command, -1)
        return True

    def canRedo(self):
        return len(self.mRedoStack) > 0

    def countRedo(self):
        return len(self.mRedoStack)

    def evalRedo(self, under_patronage = False):
        if not under_patronage and self.mPatronage:
            return self.mPatronage._evalRedo(self)

        next_step, command = self.mRedoStack.pop()
        self.mChangeStack.append((self.mCurrentStep, command))
        assert (self.mCurrentStep < next_step
            or (self.mCurrentStep == next_step
                and isinstance(command, PatronnedMasterStepCommand)))
        assert not RT_Guard.isFree()

        if not self.onOperationStart(command, +1):
            return False

        try:
            self.mCurrentStep = next_step
            command.doIt(self)
        finally:
            self.onOperationEnd(command, +1)
        return True

    def inOperation(self):
        return self.mInOperation > 0

    def pushOperation(self):
        if self.mInOperation > 0:
            raiseRuntimeError("OP in OP!!!")
        self.mInOperation += 1

    def popOperation(self):
        self.mInOperation -= 1

    def _makePatronedMasterCmd(self, patronage, command, master_obj):
        assert False

    def _dropCmd(self, command):
        for idx in range(len(self.mChangeStack)):
            if self.mChangeStack[idx][1] is command:
                _deactivateOneFromStack(self.mChangeStack, idx)
                return
        for idx in range(len(self.mRedoStack)):
            if self.mRedoStack[idx][1] is command:
                _deactivateOneFromStack(self.mRedoStack, idx)
                return

#================================
#================================
class PatronnedMasterStepCommand(StepCommand):
    def __init__(self, patronage, base_command):
        StepCommand.__init__(self)
        self.mPatronage  = patronage
        self.mBaseCmd    = base_command
        self.mBaseCmd._setpatron_agent(self)

    def getCmdName(self):
        return self.mBaseCmd.getCmdName()

    def getWeight(self):
        return self.mBaseCmd.getWeight()

    def deactivate(self):
        self.mBaseCmd.deactivate()

    def _regOn(self, base_command):
        assert self.mBaseCmd is base_command
        self.mPatronage._regOn(self)

    def _regOff(self, base_command):
        assert self.mBaseCmd is base_command
        self.mBaseCmd.mpatron_agent = None
        self.mPatronage._regOff(self)

    def getpatron_agent(self):
        return self

    def getDescr(self):
        return self.mBaseCmd.getDescr()

#================================
class StepPatronage:
    def __init__(self, master, slave):
        self.mMaster   = master
        self.mSlave    = slave
        self.mCountOp  = 0
        self.mMaster._setPatronage(self)
        self.mSlave._setPatronage(self)
        self.mTerminated = False

    def _regOn(self, patron_agent):
        self.mCountOp += 1

    def _regOff(self, patron_agent):
        self.mMaster._dropCmd(patron_agent)
        self.mSlave._dropCmd(patron_agent.mBaseCmd)
        self.mCountOp -= 1
        if self.mCountOp == 0:
            if not self.mTerminated:
                self.deactivate()

    def deactivate(self):
        if self.mTerminated:
            return
        self.mTerminated = True
        self.mMaster._setPatronage(None)
        self.mSlave._setPatronage(None)

    def evalCommand(self, command, master_obj):
        cmd_master = self.mMaster._makePatronedMasterCmd(
            self, command, master_obj)
        if cmd_master is None:
            print("Missed cmd_master under patronage!", file = sys.stderr)
            return False
        if not self.mSlave.evalCommand(command, True):
            return False
        self.mMaster.onOperationStart(cmd_master, 0)
        self.mMaster.mChangeStack.append(
            (self.mMaster.mCurrentStep, cmd_master))
        _deactivateStack(self.mMaster.mRedoStack)
        self.mMaster.mRedoStack = []
        self.mMaster.onOperationEnd(cmd_master, 0)
        return True

    def _evalCommand(self, ctrl, command):
        if ctrl is not self.mMaster:
            self.deactivate()
        return self.mMaster.evalCommand(command, True)

    def _evalUndo(self, ctrl):
        if len(self.mMaster.mChangeStack) > 1:
            prev_step, cmd_master = self.mMaster.mChangeStack[-1]
            if (isinstance(cmd_master, PatronnedMasterStepCommand)
                    and len(self.mSlave.mChangeStack) > 0
                    and self.mSlave.mChangeStack[-1][1]
                    is cmd_master.mBaseCmd):
                ret = self.mSlave.evalUndo(True)
                self.mMaster.evalUndo(True)
                return ret
            if ctrl is self.mMaster:
                return self.mMaster.evalUndo(True)
        print("Failed to undo under patronage:", self.mMaster.mChangeStack,
            file = sys.stderr)
        self.deactivate()
        return ctrl.evalUndo(True)

    def _evalRedo(self, ctrl):
        if len(self.mMaster.mRedoStack) > 0:
            prev_step, cmd_master = self.mMaster.mRedoStack[-1]
            if (isinstance(cmd_master, PatronnedMasterStepCommand)
                    and len(self.mSlave.mRedoStack) > 0
                    and self.mSlave.mRedoStack[-1][1] is cmd_master.mBaseCmd):
                ret = self.mSlave.evalRedo(True)
                self.mMaster.evalRedo(True)
                return ret
            if ctrl is self.mMaster:
                return self.mMaster.evalRedo(True)
        print("Failed to redo under patronage:", self.mMaster.mRedoStack,
            file = sys.stderr)
        self.deactivate()
        return ctrl.evalRedo(True)

#================================
