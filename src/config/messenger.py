# -*- coding: utf-8 -*-
import sys

sMessagesV = {
    "*":              ("", 0),
    #=================
    #=================
    # UI elements
    #=================
    "menu.title":      ("Вероника",                      0),
    "menu.version":    ("Версия: %s",                       1),
    "menu.vendor":     (''' trf@ya.ru ''', 0),
    "menu.file":       ("Пакет", 0),
    "menu.edit":       ("Pедактирование", 0),
    "menu.help":       ("Пoмощь", 0),
    "menu.prefs":      ("Настройки", 0),
    "menu.about":      ("О пpограмме", 0),
    "menu.save":       ("Сохранить", 0),
    "menu.title.proj": ("Veronica: %s",                      1),

    "menu.exit":          ("Завершить работу", 0),
    "menu.drop-changes":  ("Сбросить изменения", 0),
    "menu.save.all":  ("Сохранить всё", 0),
    "menu.undo":      ("Откатить изменение", 0),
    "menu.redo":      ("Накатить изменение", 0),
    "tab.repos":     ("На текущий элемент", 0),
    "tab.save":      ("Сохранить изменения", 0),

    "img.save.tip":  ("Сохранить разметку изображения", 0),
    "img.clear-changes.tip": ("Сбросить модификации в разметке", 0),
    "img.undo.tip":      ("Откатить изменение", 0),
    "img.redo.tip":      ("Накатить изменение", 0),
    "img.to-learn":      ("В разметку для обучения", 0),
    "img.out-of-learn":  ("Убрать разметку для обучения", 0),
    "img.out-of-learn.confirm": ("Подтвердите снятие разметки для обучения\n" +
        "Результат операции необратим", 0),
    "img.out-of-learn.yes": ("Снять", 0),
    "img.out-of-learn.no":  ("Отказаться", 0),

    "markup.path.no": ("no", 0),
    "markup.path.type": ("тип", 0),
    "markup.path.points": ("точки", 0),
    "markup.path.type.tip": ("тип объекта разметки", 0),

    "markup.path.type.vesicula": ("везикула", 0),
    "markup.path.type.v-seg":   ("сегмент везикулы", 0),
    "markup.path.type.barrier": ("линия помех", 0),
    "markup.path.type.blot": ("клякса", 0),
    "markup.path.type.dirt": ("грязь", 0),

    "markup.path.create.tip": ("Новый объект разметки", 0),
    "markup.path.delete.tip": ("Удалить объект разметки", 0),

    "menu.markup.done": ("Разметка для обучения готова", 0),
    "dir.round.tip":    ("Выбор режима", 0),
    "dir.round.all":    ("Все изображения", 0),
    "dir.round.learn":  ("Разметка для обучения", 0),

    "img.entry.tab.info":  ("Снимок", 0),
    "img.entry.tab.learn": ("Разметка", 0),

    "info.edit.quality.title": ("Качество", 0),
    "info.edit.quality.tip": ("Оценка качества (0-отсутствие оценки)", 0),
    "info.to.learn": ("В разметку для обучения", 0),
    "info.edit.note.title": ("Заметка", 0),
    "info.edit.mark.tip": ("Тип заметки", 0),
    "info.edit.mark.title": ("Тип заметки", 0),

    "img.not.avail":    ("Изображение недоступно", 0),
    "img.not.found":    ("Изображение не найдено", 0),
    "img.zoom.tip":     ("Масштаб изображения", 0),
    "img.opacity.tip":  ("Прозрачность изображения", 0),
    "mode.changing.tip":      ("Несохранёные изменения", 0),
    "mode.runtime.tip":       ("Программа работает, ждите", 0),

    "keyboard.cfg.error":     ("Ошибки в файле настройкe клавиатуры",  0),
    "keyboard.cfg.cancel":    ("Настройки клавиатуры сброшены",        0),
    "keyboard.cfg.file":      ("Файл %s",                              1),
    "keyboard.cfg.file.bad":  ("Ошибка чтения файла",                  0),
    "keyboard.cfg.file.none": ("Файл не найден",                       0),
    "keyboard.cfg.line.bad":  ("Строка %d: неправильная инструкция",   1),
    "keyboard.cfg.key.bad":   ("Строка %d: "
        "неправильнoe обозначение клавиши",    1),
    "keyboard.cfg.key.dup":   ("Строка %d: "
        "повторное использование клавиши",     1),
    "keyboard.cfg.cmd.bad":   ("Строка %d: "
        "незарегистрированная команда %s",     2),

    "prefs.title":             ("Настройки", 0),
    "prefs.file.kbd":          ("Конфигурация горячих клавиш", 0),
    "prefs.ext-edit":          ("Внешний текстовый редактор", 0),
    "prefs.ext-edit.tip":      ("Для прямого редактирования "
        "графических индексов", 0),
    "prefs.user":              ("Ваше имя", 0),
    "prefs.save":              ("Сохранить", 0),
    "prefs.close":             ("Закрыть", 0),
    "prefs.edit.kbd":
        ("Редактировать конфигурацию горячих клавиш", 0),
    "prefs.edit.slist":
        ("Редактировать конфигурацию пакетов поиска и замены", 0),

    "vpatch.dial.value":            ("%d°", 1),
    "vpatch.no.patch":              ("Мини-блок не задан", 0),
    "vpatch.no.markup":             ("Разметка не представлена", 0),
    "vpatch.markup.empty":          ("Размечено: пусто", 0),
    "vpatch.markup.one":            ("Размечено: один сегмент", 0),
    "vpatch.markup.colision":       ("Размечено: %d сегментов", 1),
    "vpatch.markup.error":          ("Ошибка при отработке разметки", 0),
    "vpatch.angle.recalc":          ("Пересчитать", 0),

    "vpatch.sup.title":             ("Вероника: мини-блок", 0),
    "tip.vpatch.sup.raise":         ("Активизировать окно мини-блока", 0),
    "tip.veronica.raise":           ("Активизировать основное окно", 0),

    "action.failed":     ("Действие ничего не изменило (%s)", 1),
    "action.tab.failed": ("В текущем режиме действие не актуально (%s)", 1),
    "action.lost":       ("действие не предусмотрено, "
        "обратитесь к разработчикам (%s)", 1),
    "action.delete.failed": ("В текущем режиме удаление не актуально", 0),

    "fatal":      ("Тяжёлая ошибка, обратитесь к разработчикам", 0),
    "not-found":  ("Незарегистрированное сообщение '%s', "
        "обратитесь к разработчикам", 1),
    "xml.parse.problems":   ("Ошибки в XML-файле %s", 1),
    "xml.invalid.top":      ("Неправильно оформлен корневой тег %s", 1),
    "xml.at.line":          ("Строка %d: ", 1),
}

#=================================
sAppMessages = sMessagesV

def resetMsgSetup(message_dict):
    global sAppMessages
    sAppMessages = message_dict


#=================================
sNotFound = set()
def msg(code, arg = None):
    global sAppMessages, sNotFound
    if code not in sAppMessages.keys():
        if code not in sNotFound:
            print("MSG: not found code", code, file = sys.stderr)
            sNotFound.add(code)
        return msg("not-found", code)
    txt, num = sAppMessages[code]
    if num == 0:
        assert not arg
        return txt
    try:
        return txt % arg
    except Exception:
        print("msg problem for code=%s arg=%s" % (code, str(arg)),
            file = sys.stderr)
    return "???"
