# -*- coding: utf-8 -*-
import regex, unicodedata

#===================================================
def _loadCharMap():
    char_map_data = '''
        ß=>ss æ=>ae œ=>oe þ=>th ð=>d đ=>d  ø=>o ł=>l ı=>i ſ=>s
        ẞ=>Ss Æ=>Ae Œ=>Oe Þ=>Th Ð=>D Đ=>D  Ø=>O Ł=>L

        і=>и ѣ=>е ѳ=>ф ѵ=>и є=>е ї=>и ў=>у ѕ=>з
        І=>И Ѣ=>Е Ѳ=>Ф Ѵ=>И Є=>Е Ї=>И Ў=>У Ѕ=>З
        џ=>дж ј=>й љ=>ль њ=>нь ђ=>дь ћ=>ть
        Џ=>Дж Ј=>Й Љ=>Ль Њ=>Нь Ђ=>Дь Ћ=>Ть

        ѡ=>о ѻ=>о ѽ=>о ѿ=>от ѥ=>е ѧ=>я ѩ=>я ѫ=>у ѭ=>ю ѹ=>у ѯ=>кс ѱ=>пс
        Ѡ=>О Ѻ=>О Ѽ=>О Ѿ=>От Ѥ=>Е Ѧ=>Я Ѩ=>Я Ѫ=>У Ѭ=>Ю Ѹ=>У Ѯ=>Кс Ѱ=>Пс

        ґ=>г ғ=>г ҕ=>г
        Ґ=>Г Ғ=>Г Ҕ=>Г
        қ=>к ҝ=>к ҟ=>к ҡ=>к ӄ=>к
        Қ=>К Ҝ=>К Ҟ=>К Ҡ=>К Ӄ=>К
        ң=>н ҥ=>н ӈ=>н ӊ=>н
        Ң=>Н Ҥ=>Н Ӈ=>Н Ӊ=>Н
        ҳ=>х һ=>х ҷ=>ч ҹ=>ч ӌ=>ч җ=>ж ҙ=>з ҫ=>с ҭ=>т
        Ҳ=>Х Һ=>Х Ҷ=>Ч Ҹ=>Ч Ӌ=>Ч Җ=>Ж Ҙ=>З Ҫ=>С Ҭ=>Т
        ә=>а ӕ=>а ө=>о ү=>у ұ=>у
        Ә=>А Ӕ=>А Ө=>О Ү=>У Ұ=>У

        α=>a β=>b γ=>g δ=>d ε=>e ζ=>z η=>h θ=>q ι=>i κ=>k λ=>l μ=>m ν=>n
        Α=>A Β=>B Γ=>G Δ=>D Ε=>E Ζ=>Z Η=>H Θ=>Q Ι=>I Κ=>K Λ=>L Μ=>M Ν=>N
        ξ=>x ο=>o π=>p ρ=>r ς=>s σ=>s τ=>t υ=>u ϕ=>f χ=>c ψ=>y ω=>w
        Ξ=>X Ο=>O Π=>P Ρ=>R Σ=>S      Τ=>T Υ=>U Φ=>F Χ=>C Ψ=>Y Ω=>W
        ϐ=>b ϑ=>q φ=>f ϖ=>p
    '''

    ret = dict()
    for comb_sym in range(0x300, 0x370):
        ret[chr(comb_sym)] = ""
    for instr in char_map_data.split():
        letter, q, dest = instr.partition("=>")
        assert len(letter) == 1
        assert letter not in ret
        ret[letter] = dest
    return ret

#===================================================
class UniText:

    sPlainString = regex.compile(r'^[\.\,\-\:\;\+\-\=\s0-9A-Za-zА-я]*$')
    sNoAllNormSymbols = regex.compile('[йЙёЁ]+')
    sNoNormSymbols = regex.compile('[йЙ]+')

    @classmethod
    def decompositeDiacritics(cls, text):
        if cls.sPlainString.match(text) is not None:
            return text
        return cls._process(text, cls.sNoAllNormSymbols, cls.stdNormalize)

    @classmethod
    def transliterate(cls, text, max_len = None):
        if cls.sPlainString.match(text) is not None:
            return text
        ret = cls._process(text, cls.sNoNormSymbols, cls.transNormalize)
        if max_len is not None and len(ret) > max_len:
            ret = ret[:(max_len - 3)] + "..."
        return ret

    #===================================================
    # Implementation details
    #===================================================
    @staticmethod
    def _process(text, no_norm_patt, apply_f):
        ret = []
        idx = 0
        while True:
            pos = no_norm_patt.search(text, idx)
            if pos is not None:
                if pos.start() > 0:
                    ret.append(apply_f(text[idx:pos.start()]))
                ret.append(text[pos.start():pos.end()])
                idx = pos.end()
                continue
            ret.append(apply_f(text[idx:]))
            break
        return "".join(ret)

    @staticmethod
    def stdNormalize(text):
        return unicodedata.normalize('NFD', text)

    sExoticCharMap = _loadCharMap()

    @classmethod
    def transNormalize(cls, text):
        return "".join([cls.sExoticCharMap.get(letter, letter)
            for letter in unicodedata.normalize('NFD', text)])


#===================================================
if __name__ == "__main__":

    test_map_data = '''
        à è ì ò ù => a e i o u
        á é í ó ú ć ś ź ń => a e i o u c s z n
        â ê î ô û => a e i o u
        ã õ ñ => a o n
        ā ē ī ō ū => a e i o u
        ä ë ï ö ü => a e i o u
        å ů => a u
        č š ž ť ď ľ ň ř => c s z t d l n r
        ç ş ţ ķ ģ ņ ŗ => c s t k g n r
        ą ę į ų => a e i u

        ᾶ => a
        ἂ => a
        ἅ => a
        ἆ => a
        ἆ => a
        ᾇ => a

        groß=>gross
        cæsar=>caesar
        cœur=>coeur
        þorn=>thorn
        eða=>eda
        Đurović=>Durovic
        søster=>soster
        łęką=>leka

        всѣ=>все
        ѳѵміамъ=>фимиамъ
        краљ=>краль
        коњ=>конь
        мој=>мой
        Караџић=>Караджить
        Ђурђе=>Дьурдье
        ѓ ќ => г к

        ψυχη=>yuch
        ανθρωπος=>anqrwpos

        А й ἅ й А => А й a й А
        5̅dK0 => 5dK0
    '''

    cnt_bad = 0
    for line in test_map_data.split('\n'):
        line = line.strip()
        if not line:
            continue
        txt_from, txt_to = line.split('=>')
        txt_from, txt_to = txt_from.strip(), txt_to.strip()
        if txt_to != UniText.transliterate(txt_from):
            print("BAD transform:", txt_from, "=>",
                UniText.transliterate(txt_from), "!=", txt_to)
            print(UniText.transNormalize(txt_from))
            cnt_bad += 1
    if cnt_bad > 0:
        print("Transliteration FAILS with %d failures" % cnt_bad)
    else:
        print("Transliteration tested well")
