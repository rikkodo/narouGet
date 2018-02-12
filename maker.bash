#!/bin/bash

. config.sh
# 設定ファイル読み込み

workdir="tex"
tmpfile="tmp"
savePath=$SAVEFILE
# $SAVEFILEは環境変数で宣言しておく
target="data/novels.txt"

PRE_IFS=$IFS
IFS=$'\n'
# 半角スペース対策

bak="_bak.txt"
dummy="_dummy.txt"

update=`date +"%Y/%m/%d_%H:%M:%S"`

echo "FILE-FORMAT: ncode,fileName[,LastUpdate[,LastVolume]]"
echo "Updating: $update"

texlog="/dev/null"

FORCE=""

while [ $# -gt 0 ] ;
do
    echo "$#"
    case ${1} in
        -F) export FORCE="TRUE"; shift;;
        *) echo "Usage $0 [-F]"; exit 0;;
    esac
done

echo "FORCE ${FORCE}"

# ターゲットファイルを残しておく
cp ${target} "${target}${bak}"
if [ -e "${target}${dummy}" ] ;
then
    rm "${target}${dummy}"
fi

for i in `cat $target`
do
    iupdate=${update}
    ncode=`echo $i | awk -F ',' '{print $1}'`
    fname=`echo $i | awk -F ',' '{print $2}' | sed -e "s/ /_/g"`
    lastUpdate=`echo $i| awk -F ',' '{print $3}'`
    volume=`echo $i| awk -F ',' '{print $4}'`
    if [ "$FORCE" = "TRUE" ] ;
    then
        lastUpdate=""
        volume=""
    fi

    if [ ! -e "${savePath}/${fname}" ] ;
    then
        mkdir "${savePath}/${fname}"
    fi
    echo
    echo "${ncode}..."
    cd $workdir
    rm ${tmpfile}*
    if [ "${volume}" = "" ] ;
    then
        volume=1
    fi
    while :
    do
        echo "Volume ${volume}"
        python ../getFiles.py ${ncode} ${volume} ${lastUpdate} > ${tmpfile}.tex
        if [ $? -ne 0 ] ;
        then
            break
        fi

        echo "LaTeX..." &&
        platex ${tmpfile}.tex >> ${texlog}&&
        platex ${tmpfile}.tex >> ${texlog}&&
        platex ${tmpfile}.tex >> ${texlog}&&
        dvipdfmx -q -p a5 ${tmpfile}.dvi >> ${texlog}&&
        mv -f "${tmpfile}.pdf" "${savePath}/${fname}/${fname}(${volume}).pdf"
        rm ${tmpfile}.*
        volume=$(expr ${volume} + 1)
    done

    # python スクリプト側で，更新なしの場合は 1 を，ページ終了の場合は 2 を返すようにする．
    if [ $? -eq 1 ];
    then
        echo "Skip \"${ncode}\""
        iupdate=${lastUpdate}
    else
        echo "Complete!"
        touch "${savePath}/${fname}"
        if [ ${volume} -gt 1 ];
        then
            volume=$(expr ${volume} - 1)
        fi
    fi
    cd ../

    echo "${ncode},${fname},${iupdate},${volume}" >> ${target}${dummy}
done

mv ${target}${dummy} ${target}

IFS=$PRE_IFS
exit 0
