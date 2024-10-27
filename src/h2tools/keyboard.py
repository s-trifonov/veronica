# -*- coding: utf-8 -*-
import sys
from io import StringIO

from PyQt5 import QtCore
from config.messenger import msg
from config.ver_keys import sKeyboardCommandList
from .utils import FileControlHandler, getExceptionValue
#================================
class KeyboardSupport:
    sDescr2Key = {
        "ESC":        0x01000000,
        "TAB":        0x01000001,
        "BACKSPACE":  0x01000003,
        "ENTER":      0x01000005,
        "INS":        0x01000006,
        "DEL":        0x01000007,
        "HOME":       0x01000010,
        "END":        0x01000011,
        "LEFT":       0x01000012,
        "UP":         0x01000013,
        "RIGHT":      0x01000014,
        "DOWN":       0x01000015,
        "PGUP":       0x01000016,
        "PGDOWN":     0x01000017,
        "F1":         0x01000030,
        "F2":         0x01000031,
        "F3":         0x01000032,
        "F4":         0x01000033,
        "F5":         0x01000034,
        "F6":         0x01000035,
        "F7":         0x01000036,
        "F8":         0x01000037,
        "F9":         0x01000038,
        "F10":        0x01000039,
        "F11":        0x0100003a,
        "F12":        0x0100003b,
        "$":          0x24,
        "%":          0x25,
        "&":          0x26,
        "(":          0x28,
        ")":          0x29,
        "+":          0x2b,
        "0":          0x30,
        "1":          0x31,
        "2":          0x32,
        "3":          0x33,
        "4":          0x34,
        "5":          0x35,
        "6":          0x36,
        "7":          0x37,
        "8":          0x38,
        "9":          0x39,
        "?":          0x3f,
        "@":          0x40,
        "A":          0x41,
        "B":          0x42,
        "C":          0x43,
        "D":          0x44,
        "E":          0x45,
        "F":          0x46,
        "G":          0x47,
        "H":          0x48,
        "I":          0x49,
        "J":          0x4a,
        "K":          0x4b,
        "L":          0x4c,
        "M":          0x4d,
        "N":          0x4e,
        "O":          0x4f,
        "P":          0x50,
        "Q":          0x51,
        "R":          0x52,
        "S":          0x53,
        "T":          0x54,
        "U":          0x55,
        "V":          0x56,
        "W":          0x57,
        "X":          0x58,
        "Y":          0x59,
        "Z":          0x5a,
        "[":          0x5b,
        "\\":         0x5c,
        "]":          0x5d,
        "_":          0x5f}

    sLetters_Rus = u"йцукенгшщзфывапролдячесмит".upper()
    sLetters_Eng = "qwertyuiopasdfghjklzxcvbnm".upper()

    sRus2Key  = None

    @classmethod
    def _getKey(cls, sym):
        if cls.sRus2Key is None:
            cls.sRus2Key = {rus_sym: cls.sDescr2Key[eng_sym]
                for rus_sym, eng_sym in
                zip(cls.sLetters_Rus, cls.sLetters_Eng)}
        return cls.sRus2Key.get(sym)

    #================================
    @classmethod
    def parseKeyDescr(cls, key_descr):
        modifiers = 0
        ff = key_descr.upper().split('-')
        for mod, mcode in (("ALT", QtCore.Qt.AltModifier),
                ("CTRL", QtCore.Qt.ControlModifier),
                ("SHIFT", QtCore.Qt.ShiftModifier)):
            if len(ff) > 1 and ff[0] == mod:
                del ff[0]
                modifiers |= int(mcode)
        if len(ff) != 1:
            return None
        if len(ff) == 1 and ff[0] in cls.sDescr2Key:
            return (modifiers, cls.sDescr2Key[ff[0]])
        return None

    #================================
    @classmethod
    def getKeyData(cls, evt):
        if evt.text():
            k = cls._getKey(evt.text().upper())
            if k is not None:
                return (int(evt.modifiers()), k)
        return (int(evt.modifiers()), evt.key())

    #================================
    sAvailableCommands = set()
    for instr in sKeyboardCommandList:
        command = instr[0]
        if not command.startswith('@'):
            assert command not in sAvailableCommands, (
                "Key command duplication: " + command )
            sAvailableCommands.add(command)

    #================================
    sFControl = None
    sKeyMap   = None
    sLastAction    = None

    @classmethod
    def checkKbdFile(cls, fname):
        if (cls.sFControl is not None
                and cls.sFControl.sameFName(fname)
                and not cls.sFControl.hasConflict()):
            return None
        cls.sFControl = FileControlHandler(fname, "kbd")
        cls.sFControl.resetControl()
        cls.sKeyMap   = None
        if cls.sFControl.noFile():
            print("No keyboard file %s" % fname, file = sys.stderr)
            return None
        key_map = dict()
        try:
            with open(fname, "r", encoding="utf-8") as inp:
                line_no = 0
                for ln in inp:
                    line_no += 1
                    instr, q, comment = ln.partition('#')
                    instr = instr.strip()
                    if not instr:
                        continue
                    key_descr, q, command = instr.partition('=')
                    if q != '=' or len(command.split()) != 1:
                        return msg("keyboard.cfg.line.bad", line_no)
                    key_descr = key_descr.strip()
                    key = cls.parseKeyDescr(key_descr)
                    command = command.strip()
                    if key is None:
                        return msg("keyboard.cfg.key.bad", line_no)
                    if key in key_map:
                        return msg("keyboard.cfg.key.dup", line_no)
                    if command not in cls.sAvailableCommands:
                        return msg("keyboard.cfg.cmd.bad", (line_no, command))
                    key_map[key] = (command,
                        "%s = %s" % (key_descr, command))

        except Exception:
            getExceptionValue()
            return msg("keyboard.cfg.file.bad")
        cls.sKeyMap = key_map
        cls.sLastAction    = None
        print("Keyboard file %s loaded" % fname, file = sys.stderr)
        return None

    #================================
    @classmethod
    def processKeyEvent(cls, evt):
        if cls.sKeyMap is None:
            return None
        command = cls.sKeyMap.get(cls.getKeyData(evt))
        if command == "cmd-repeate":
            return cls.sLastAction
        if command is not None:
            cls.sLastAction = command
        return command

    #================================
    @classmethod
    def formDoc(cls):
        title = msg("repr.title.keys")
        rep = StringIO()
        print(f'<h2>{title}</h2>', file = rep)
        tab_started = False
        for instr in sKeyboardCommandList:
            command = instr[0]
            if command == "@Head1":
                if tab_started:
                    print('</table>', file = rep)
                    tab_started = False
                print('<h3>' + ' '.join(instr[1:]) + '</h3>', file = rep)
                continue
            if not tab_started:
                print('<table class="help">', file = rep)
                tab_started = True
            if command.startswith('@'):
                if command == "@Spacer":
                    print('<tr><td colspan="2">&nbsp;</td></tr>', file = rep)
                    continue
                assert command in ("@Head2", "@Head3", "@Comment"), (
                    "Missed command: " + command)
                cmd_class = command[1:].lower()
                print(f'<tr><td colspan="2" class="{cmd_class}">'
                    + ' '.join(instr[1:]) + '</td></tr>', file = rep)
                continue
            print('<tr><td class="spec">' + command
                + '</td><td class="descr">' + ' '.join(instr[1:])
                + '</td></tr>', file = rep)
        if tab_started:
            print('</table>', file = rep)
        return title, rep.getvalue()
