# -*- coding: utf-8 -*-
import sys, regex
from .html_ent import HTML_ENTITIES
#===================================================
def _procTagName(name):
    if name == "unparseable":
        return "<непонятно>"
    return name

#===================================================
def _proc_ERR_TAG_NAME_MISMATCH(match):
    tag1  = _procTagName(match.group(1))
    tag2  = _procTagName(match.group(3))
    if tag1 in ("body", "html") or tag2 in ("body", "html"):
        return "Неправильное закрытие тега"

    return "Вместо </%s> ожидалось закрытие </%s>" % (tag2, tag1)

def _proc_ERR_TAG_NOT_FINISHED(match):
    tag1  = _procTagName(match.group(1))
    return "Неправильно открытый тег <%s>" % (tag1)

def _proc_ERR_GT_REQUIRED(match):
    tag1  = _procTagName(match.group(1))
    return u"Не найден конец тега <%s>" % tag1

def _proc_ERR_UNDECLARED_ENTITY(match):
    entity = "&" + match.group(1) + ";"
    if entity not in HTML_ENTITIES:
        return "Не зарегистрированный код %s" % (entity)
    return "Перекодируйте %s %s" % (entity,
        HTML_ENTITIES[entity])

#===================================================
class XML_ErrTranslator:
    sAll = []
    sFailed = set()

    #===================================================
    sAll.append((_proc_ERR_TAG_NAME_MISMATCH, regex.compile(
        r"Opening and ending tag mismatch: (\S+) line (\d+) and (\S+)")))
    sAll.append((_proc_ERR_TAG_NOT_FINISHED, regex.compile(
        r"Premature end of data in tag (\S+) line (\d+)")))
    sAll.append((_proc_ERR_GT_REQUIRED, regex.compile(
        r"Couldn\'t find end of Start Tag (\S+) line (\d+)")))
    sAll.append((_proc_ERR_UNDECLARED_ENTITY, regex.compile(
        r"Entity \'(\S+)\' not defined")))

    #===================================================
    sAll.append((lambda m: "Плохое имя элемента",
        regex.compile("invalid element name")))

    sAll.append((lambda m: "Плохое название атрибута",
        regex.compile("error parsing attribute name")))

    sAll.append((lambda m: "Ожидается символ '%s'" % m.group(1),
        regex.compile(r"EntityRef\: expecting \'([^\']+)\'")))

    sAll.append((lambda m: "Нет такого кода",
        regex.compile(r"EntityRef\: no name")))

    sAll.append((lambda m: "Неправильно оформлены атрибуты тега",
        regex.compile("attributes construct error")))

    sAll.append((lambda m: "Плохой код",
        regex.compile(r"CharRef\: invalid xmlChar value")))

    sAll.append((lambda m: "Плохой десятичный код",
        regex.compile(r"CharRef\: invalid decimal value")))

    sAll.append((lambda m: "Плохой 16-ричный код",
        regex.compile(r"CharRef\: invalid hexadecimal value")))

    sAll.append((lambda m: "Неправильно оформленный атрибут",
        regex.compile("Specification mandates value for attribute")))

    sAll.append((lambda m: "Неожиданный конец документа",
        regex.compile("Extra content at the end of the document")))

    sAll.append((lambda m: "Ожидается закрытие тега '>'",
        regex.compile(r"expected \'>\'")))

    sAll.append((lambda m: "Значение атрибута: не хватает кавычки",
        regex.compile("AttValue: \" or ' expected")))

    sAll.append((lambda m: "Неправильный символ '%s' в значении атрибута"
        % m.group(1),
        regex.compile(
            r"Unescaped '([^\']+)' not allowed in attributes values")))

    sAll.append((lambda m: "Атрибут %s определён больше одного раза"
        % m.group(1),
        regex.compile(r"Attribute (\w+) redefined")))
    #===================================================
    sRegExp_LinePos = regex.compile(r"\, line (\d+)\, column (\d+)\s*")

    @classmethod
    def translate(cls, message):
        line_no = 0
        idx = message.rfind(", line ")
        if idx >= 0:
            q = cls.sRegExp_LinePos.match(message[idx:])
            if q is not None:
                line_no = int(q.group(1))
                message = message[:idx]
        for proc_f, reg_exp in cls.sAll:
            match = reg_exp.search(message.strip())
            if match:
                m = proc_f(match)
                return (line_no, m)
        if message[:30] not in cls.sFailed:
            cls.sFailed.add(message[:30])
            print("Translation HTML fail:", message, file = sys.stderr)
        return (line_no, message)

    #===================================================
    @classmethod
    def parseXMLErrors(cls, err_log):
        ret = []
        for err in err_log:
            if len(ret) > 5:
                ret.append("...(ещё ошибки)")
                break
            line, message = err.line, err.message
            msg1 = cls.translate(message)[1]
            if msg1 != message:
                message = msg1
            else:
                message = "[%s] %s" % (err.type_name, message)
            ret.append(u"Строка %d: %s" % (line, message))
        return ret

#===================================================
