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
             ['♡', '$\\heartsuit$']]
    for i in match:
        string = string.replace(i[0], i[1])
    return string


def replaceRet(string):
    string = string.replace(("\r" or "\r\n"), "\n")
    string = string.replace("\n", "　\\par\n")
    return string


def main(ncode, lastUpdate):
    [title, author, page, novelUpdate] = getInfo(ncode)
    if IGNORE_UPDATE != 1:
        if novelUpdate < lastUpdate:
            print >> sys.stderr, "%s is already up-to-date." % title
            print >> sys.stderr, "Last novel update: %s" % novelUpdate
            print >> sys.stderr, "Last file update: %s" % lastUpdate
            exit(1)
    print >> sys.stderr, "UPDATE %s." % title
    header(title, author, ncode)
    pages(ncode, page)
    footer()
    return 0


def header(title, author, ncode):
    if MODE == LATEX:
        # しおり
        # http://osksn2.hep.sci.osaka-u.ac.jp/~taku/osx/latex_bookmarks.html
        line = """\\documentclass[a5j, titlepage, 12pt]{tbook}
\\usepackage[dvipdfmx]{hyperref}
\\usepackage{pxjahyper}
\\title{%s}
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
""" % (title, author)
        # landscape ?
        print line
    else:
        print "Title: %s  Author: %s" % (title, author)

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
    addr = NAROUAPI + "?out=json&ncode=" + ncode
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


def pages(ncode, page):
    # 各ページの取得
    for i in range(1, page + 1):
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


def footer():
    if MODE == LATEX:
        print "\\end{document}"
    else:
        print ""
    return 0

if __name__ == "__main__":
    argLen = 2
    if len(sys.argv) != argLen and len(sys.argv) != argLen + 1:
        print >> sys.stderr, "Usage: %s NCODE [LAST-UPDATE]" % sys.argv[0]
        print >> sys.stderr, "NULL LAST-UPDATE: force UPDATE"
        print >> sys.stderr, "LAST-UPDATE FORMAT: %%Y/%%m/%%d_%%H:%%M:%%S"
        exit(1)
    if len(sys.argv) == 2:
        IGNORE_UPDATE = 1
        print >> sys.stderr, "FORCE_UPDATE"
    ncode = sys.argv[1]
    lastUpdate = ""
    if len(sys.argv) == argLen + 1:
        lastUpdate = sys.argv[2]
        lastUpdate = datetime.datetime.strptime(lastUpdate,
                                                "%Y/%m/%d_%H:%M:%S")
    if DEBUG >= 1:
        print lastUpdate, IGNORE_UPDATE
    main(ncode, lastUpdate)
