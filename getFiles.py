# -*- coding: utf-8 -*-

import sys
import urllib2
import time
import HTMLParser
import copy
import json
import pprint
import datetime

PAUSE = 0

NAROUADDR = "http://ncode.syosetu.com/"
NAROUAPI = "http://api.syosetu.com/novelapi/api/"

DEBUG = 0

NOMAL = 0
LATEX = 1
MODE = LATEX
IGNORE_UPDATE = 0
PAGE_PAR_VOL = 25


class NarouParser(HTMLParser.HTMLParser):
    # http://ymotongpoo.hatenablog.com/entry/20081211/1228985067
    FLAG_SUBTITLE = "SUBTITLE"
    subtitle = ""
    main = ""
    FLAG = []
    # ["TAG", "ATT[0]", "ATT[1]", "FLAG_NAME", DATA, EXP]
    # [    0,        1,        2,           3,    4,   5]
    TAG = 0
    AT0 = 1
    AT1 = 2
    FLAG_NAME = 3
    DATA = 4
    INITIAL = 5
    searchDatas = []

    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        return None

    # 引数のフラグ名に合致するDATA部を返す．
    def searchData(self, name):
        for data in self.searchDatas:
            if data[self.FLAG_NAME] == name:
                return data[self.DATA]
        print >> sys.stderr, "FLAG_NAME %s not found." % name
        return ""

    # テキスト作成部をすべて初期化する．
    def refresh(self):
        for data in self.searchDatas:
            initial = copy.deepcopy(data[self.INITIAL])
            data[self.DATA] = copy.deepcopy(initial)
        return 0

    # 開始タグ受信．処理対象ならばフラッグ ON
    def handle_starttag(self, tagname, attribute):
        for data in self.searchDatas:
            if tagname == data[self.TAG]:
                for i in attribute:
                    if data[self.AT0] == "" or i[0].lower() == data[self.AT0]:
                        if data[self.AT1] == "" or i[1].lower() == data[self.AT1]:
                            if DEBUG >= 1:
                                print i
                            if DEBUG >= 2:
                                print "IN_sub"
                            self.FLAG.append(data[self.FLAG_NAME])
        return 0

    # 終了タグ受信．処理中タグならばフラッグ OFF
    def handle_endtag(self, tagname):
        for data in self.searchDatas:
            if tagname == data[self.TAG] and data[self.FLAG_NAME] in self.FLAG:
                if DEBUG >= 2:
                    print "OUT_sub"
                self.FLAG.remove(data[self.FLAG_NAME])
        return 0

    # タグ内データ受信．出力．
    def handle_data(self, inside):
        for data in self.searchDatas:
            if data[self.FLAG_NAME] in self.FLAG:
                if DEBUG >= 5:
                    print data
                data[self.DATA] += str(inside)


# ヘッダ部のパース
class HeadParser(NarouParser):
    searchDatas = [["p", "class", "novel_title", "TITLE", "", "", "小説タイトル"],
                   ["div", "id", "novel_ex", "EXPERIMENT", "", "", "説明"]]

    def __init__(self):
        NarouParser.__init__(self)
        return None

    def output(self):
        print self.searchData("TITLE")
        print self.searchData("EXPERIMENT")
        return 0

    def outputTex(self):
        section = self.searchData("TITLE")
        section = replaceHTML(section)
        print "\\clearpage"
        print "\\section*{%s}" % section
        print "\\addcontentsline{toc}{section}{%s}" % section

        main = self.searchData("EXPERIMENT")
        main = replaceHTML(main)
        main = replaceRet(main)
        print main

        return 0


# ページ内のパース
class PageParser(NarouParser):
    searchDatas = [["p", "", "novel_subtitle", "SUBTITLE", "", "", "小説サブタイトル"],
                   ["div", "id", "novel_p", "PREVIOUS", "", "", "小説前書"],
                   ["div", "id", "novel_honbun", "MAIN", "", "", "小説本文"],
                   ["div", "id", "novel_a", "AFTER", "", "", "小説後書"]]

    def __init__(self):
        NarouParser.__init__(self)
        return None

    def output(self):
        print self.searchData("SUBTITLE")
        print self.searchData("PREVIOUS")
        print self.searchData("MAIN")
        print self.searchData("AFTER")
        return 0

    def outputTex(self):
        section = self.searchData("SUBTITLE")
        section = replaceHTML(section)
        print "\\clearpage"
        print "\\section*{%s}" % section
        print "\\addcontentsline{toc}{section}{%s}" % section

        preb = self.searchData("PREVIOUS")
        preb = replaceHTML(preb)
        preb = replaceRet(preb)
        print preb

        print "\n\\noindent\\hrulefill\n"

        main = self.searchData("MAIN")
        main = replaceHTML(main)
        main = replaceRet(main)
        print main

        print "\n\\noindent\\hrulefill\n"

        after = self.searchData("AFTER")
        after = replaceHTML(after)
        after = replaceRet(after)
        print after

        print "\n\\begin{flushright}"
        print "(%s)" % section
        print "\\end{flushright}\n"

        return 0


def replaceHTML(string):
    # http://osksn2.hep.sci.osaka-u.ac.jp/~naga/miscellaneous/tex/tex-tips6.html
    match = [['\\', '{\\textbackslash}'],  # 特殊文字組で使うので, \ と $ は先頭
             ['$', '\$'],
             ['%', '\%'],
             ['#', '\#'],
             ['&', '\&'],
             ['{', '\{'],
             ['}', '\}'],
             ['^', '{\\textasciitilde}'],
             ['*', '{\\textasteriskcentered}'],
             ['|', '{\\textbar}'],
             ['<', '{\\textless}'],
             ['>', '{\\textgreater}'],
             ['~', '{\\textasciicircum}'],
             ['─', '---'],
             ['_', '\_'],
             ['①', '(１)'],
             ['②', '(２)'],
             ['③', '(３)'],
             ['④', '(４)'],
             ['⑤', '(５)'],
             ['⑥', '(６)'],
             ['⑦', '(７)'],
             ['⑧', '(８)'],
             ['⑨', '(９)'],
             ['⑩', '(１０)'],
             ['⑪', '(１１)'],
             ['⑫', '(１２)'],
             ['⑬', '(１３)'],
             ['⑭', '(１４)'],
             ['⑮', '(１５)'],
             ['⑯', '(１６)'],
             ['⑰', '(１７)'],
             ['⑱', '(１８)'],
             ['⑲', '(１９)'],
             ['⑳', '(２０)'],
             ['㉑', '(２１)'],
             ['㉒', '(２２)'],
             ['㉓', '(２３)'],
             ['㉔', '(２４)'],
             ['㉕', '(２５)'],
             ['㉖', '(２６)'],
             ['㉗', '(２７)'],
             ['㉘', '(２８)'],
             ['㉙', '(２９)'],
             ['㉚', '(３０)'],
             ['㉛', '(３１)'],
             ['㉜', '(３２)'],
             ['㉝', '(３３)'],
             ['㉞', '(３４)'],
             ['㉟', '(３５)'],
             ['㊱', '(３６)'],
             ['㊲', '(３７)'],
             ['㊳', '(３８)'],
             ['㊴', '(３９)'],
             ['㊵', '(４０)'],
             ['㊶', '(４１)'],
             ['㊷', '(４２)'],
             ['㊸', '(４３)'],
             ['㊹', '(４４)'],
             ['㊺', '(４５)'],
             ['㊻', '(４６)'],
             ['㊼', '(４７)'],
             ['㊽', '(４８)'],
             ['㊾', '(４９)'],
             ['㊿', '(５０)'],
             ['0', '０'],
             ['1', '１'],
             ['2', '２'],
             ['3', '３'],
             ['4', '４'],
             ['5', '５'],
             ['6', '６'],
             ['7', '７'],
             ['8', '８'],
             ['9', '９'],
             ['Ⅰ', 'I'],
             ['ⅰ', 'i'],
             ['Ⅱ', 'II'],
             ['ⅱ', 'ii'],
             ['Ⅲ', 'III'],
             ['ⅲ', 'iii'],
             ['Ⅳ', 'IV'],
             ['ⅳ', 'iv'],
             ['Ⅴ', 'V'],
             ['ⅴ', 'v'],
             ['Ⅵ', 'VI'],
             ['ⅵ', 'vi'],
             ['Ⅶ', 'VII'],
             ['ⅶ', 'vii'],
             ['Ⅷ', 'VIII'],
             ['ⅷ', 'viii'],
             ['Ⅸ', 'IX'],
             ['ⅸ', 'ix'],
             ['Ⅹ', 'X'],
             ['ⅹ', 'x'],
             ['Ⅺ', 'XI'],
             ['ⅺ', 'xi'],
             ['Ⅻ', 'XII'],
             ['ⅻ', 'xii'],
             ['À', '{\\`{A}}'],
             ['à', '{\\`{a}}'],
             ['Á', '{\\\'{A}}'],
             ['á', '{\\\'{a}}'],
             ['Â', '{\\^{A}}'],
             ['â', '{\\^{a}}'],
             ['Ã', '{\\~{A}}'],
             ['ã', '{\\~{a}}'],
             ['Ä', '{\\"{A}}'],
             ['ä', '{\\"{a}}'],
             ['Å', '{\\AA}'],
             ['å', '{\\aa}'],
             ['Ā', '{\\={A}}'],
             ['ā', '{\\={a}}'],
             ['Æ', '{\\AE}'],
             ['æ', '{\\ae}'],
             ['Ç', '{\\c{C}}'],
             ['ç', '{\\c{c}}'],
             ['Ć', '{\\\'{C}}'],
             ['ć', '{\\\'{c}}'],
             ['Ð', '{\\DH}'],
             ['ð', '{\\dh}'],
             ['È', '{\\`{E}}'],
             ['è', '{\\`{e}}'],
             ['É', '{\\\'{E}}'],
             ['é', '{\\\'{e}}'],
             ['Ê', '{\\^{E}}'],
             ['ê', '{\\^{e}}'],
             ['Ë', '{\\"{E}}'],
             ['ë', '{\\"{e}}'],
             ['Ì', '{\\`{I}}'],
             ['ì', '{\\`{i}}'],
             ['Í', '{\\\'{I}}'],
             ['í', '{\\\'{i}}'],
             ['Î', '{\\^{I}}'],
             ['î', '{\\^{i}}'],
             ['Ï', '{\\"{I}}'],
             ['Ï', '{\\"{i}}'],
             ['ī', '{\\={\i}}'],
             ['ı', '{\\i}'],
             ['Ñ', '{\\~{N}}'],
             ['ñ', '{\\~{n}}'],
             ['Ò', '{\\`{O}}'],
             ['ò', '{\\`{o}}'],
             ['Ó', '{\\\'{O}}'],
             ['ó', '{\\\'{o}}'],
             ['Ô', '{\\^{O}}'],
             ['ô', '{\\^{o}}'],
             ['Õ', '{\\~{O}}'],
             ['õ', '{\\~{o}}'],
             ['Ö', '{\\"{O}}'],
             ['ö', '{\\"{o}}'],
             ['Ø', '{\\O}'],
             ['ø', '{\\o}'],
             ['Œ', '{\\OE}'],
             ['œ', '{\\oe}'],
             ['ß', '{\\ss}'],
             ['Ŝ', '{\\^{S}}'],
             ['ŝ', '{\\^{s}}'],
             ['Ş', '{\\c{S}}'],
             ['ş', '{\\c{S}}'],
             ['Š', '{\\v{S}}'],
             ['š', '{\\v{S}}'],
             ['Þ', '{\\TH}'],
             ['þ', '{\\th}'],
             ['Ù', '{\\`{U}}'],
             ['ù', '{\\`{u}}'],
             ['Ú', '{\\\'{U}}'],
             ['ú', '{\\\'{u}}'],
             ['Û', '{\\^{U}}'],
             ['û', '{\\^{u}}'],
             ['Ü', '{\\"{U}}'],
             ['ü', '{\\"{u}}'],
             ['Ý', '{\\\'{Y}}'],
             ['ý', '{\\\'{y}}'],
             ['Ÿ', '{\\"{Y}}'],
             ['ÿ', '{\\"{y}}'],
             ['♡', '$\\heartsuit$']]
    for i in match:
        string = string.replace(i[0], i[1])
    return string


def replaceRet(string):
    string = string.replace(("\r" or "\r\n"), "\n")
    string = string.replace("\n", "　\\par\n")
    return string


def main(ncode, lastUpdate, volume):
    [title, author, page, novelUpdate] = getInfo(ncode)
    if IGNORE_UPDATE != 1:
        if novelUpdate < lastUpdate:
            print >> sys.stderr, "%s is already up-to-date." % title
            print >> sys.stderr, "Last novel update: %s" % novelUpdate
            print >> sys.stderr, "Last file update: %s" % lastUpdate
            exit(1)

    # ノベル終了
    if PAGE_PAR_VOL * (volume - 1) > page:
        print >> sys.stderr, "%s finish!." % title
        exit(2)

    print >> sys.stderr, "UPDATE %s." % title
    header(title, author, ncode, volume)
    pages(ncode, page, volume)
    footer(title, volume)
    return 0


def header(title, author, ncode, volume):
    if MODE == LATEX:
        # しおり
        # http://osksn2.hep.sci.osaka-u.ac.jp/~taku/osx/latex_bookmarks.html
        line = """\\documentclass[a5j, titlepage, 12pt]{tbook}
\\usepackage[dvipdfmx]{hyperref}
\\usepackage{pxjahyper}
\\usepackage{pxbase}
\\usepackage[bxutf8]{inputenc}
\\usepackage[otf]{}
\\usepackage[T1]{fontenc}

\\title{%s(%d)}
\\author{%s}
\\date{\\today}

\\setlength{\\voffset}{-20truemm}
\\addtolength{\\textwidth}{40truemm}
\setlength{\hoffset}{-10truemm}
\\addtolength{\\textheight}{20truemm}

\\usepackage[expert,deluxe]{otf}
\\begin{document}
\\maketitle
\\tableofcontents
""" % (title, volume, author)
        # landscape ?
        print line
    else:
        print "Title: %s(%d) Author: %s" % (title, volume, author)

    addr = NAROUADDR + ncode + "/"
    fp = urllib2.urlopen(addr)
    html = fp.read()
    fp.close()
    parser = HeadParser()
    parser.refresh()
    parser.feed(html)
    # 出力
    if MODE == LATEX:
        parser.outputTex()
    else:
        parser.output()
    parser.close()
    return 0


def getInfo(ncode):
    addr = NAROUAPI + "?out=json&of=t-w-ga-nu&ncode=" + ncode
    if DEBUG >= 1:
        print addr
    fp = urllib2.urlopen(addr)
    html = fp.read()
    fp.close()
    if DEBUG >= 10:
        print html
    jhtml = json.loads(html)[1]
    if DEBUG >= 4:
        pprint.pprint(jhtml)
    title = jhtml["title"].encode("utf-8")
    author = jhtml["writer"].encode("utf-8")
    page = int(jhtml["general_all_no"])
    novelUpdate = jhtml["novelupdated_at"].encode("utf-8")
    novelUpdate = datetime.datetime.strptime(novelUpdate, "%Y-%m-%d %H:%M:%S")
    info = [title, author, page, novelUpdate]
    if DEBUG >= 1:
        for i in info:
            print i
    return info


def pages(ncode, page, volume):
    # 各ページの取得
    volstart = PAGE_PAR_VOL * (volume - 1) + 1
    volend = PAGE_PAR_VOL * volume

    # 最大ページ超過
    if volend > page:
        volend = page

    for i in range(volstart, volend + 1):
        print >> sys.stderr, "\rpage %d/%d" % (i, page),
        # time.sleep(PAUSE)
        addr = NAROUADDR + ncode + "/" + str(i) + "/"
        # よく失敗するので成功するまでやり直す．
        while True:
            try:
                fp = urllib2.urlopen(addr)
            except:
                time.sleep(1)
                print >> sys.stderr, "Re Try"
                continue
            else:
                break
        html = fp.read()
        fp.close()
        parser = PageParser()
        parser.refresh()
        parser.feed(html)
        # 出力
        if MODE == LATEX:
            parser.outputTex()
        else:
            parser.output()
        parser.close()

        if DEBUG >= 10:
            print html
    print >> sys.stderr, "\nComplete!"
    return 0


def footer(title, volume):
    if MODE == LATEX:
        print "\n\\begin{flushright}"
        print "%s(%d)" % (title, volume)
        print "\\end{flushright}\n"
        print "\\end{document}"
    else:
        print ""
    return 0


if __name__ == "__main__":
    argLen = 3
    subLen = 1
    if len(sys.argv) != argLen and len(sys.argv) != argLen + subLen:
        print >> sys.stderr, "Usage: %s NCODE VOLUME [LAST-UPDATE]" % sys.argv[0]
        print >> sys.stderr, "NULL LAST-UPDATE: force UPDATE"
        print >> sys.stderr, "LAST-UPDATE FORMAT: %%Y/%%m/%%d_%%H:%%M:%%S"
        exit(-1)
    ncode = sys.argv[1]
    volume = int(sys.argv[2])
    lastUpdate = ""
    if len(sys.argv) == argLen:
        IGNORE_UPDATE = 1
        print >> sys.stderr, "FORCE_UPDATE"
    elif len(sys.argv) == argLen + subLen:
        lastUpdate = sys.argv[3]
        lastUpdate = datetime.datetime.strptime(lastUpdate,
                                                "%Y/%m/%d_%H:%M:%S")
    if DEBUG >= 1:
        print lastUpdate, IGNORE_UPDATE, volume
    main(ncode, lastUpdate, volume)
