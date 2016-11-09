#!/bin/bash

workdir="tex"
tmpfile="tmp"
savePath=$SAVEFILE
# $SAVEFILEは環境変数で宣言しておく
target="data/novels.txt"

bak="_bak.txt"
dummy="_dummy.txt"

update=`date +"%Y/%m/%d_%H:%M:%S"`

echo "FILE-FORMAT: ncode,fileName[,LastUpdate]"
echo "Updating: $update"

texlog="/dev/null"

# ターゲットファイルを残しておく
cp ${target} ${target}${bak}
rm ${target}${dummy}
for i in `cat $target`
do
    iupdate=${update}
    ncode=`echo $i | awk -F ',' '{print $1}'`
    fname=`echo $i | awk -F ',' '{print $2}'`
    lastUpdate=`echo $i| awk -F ',' '{print $3}'`
    echo
    echo "${ncode}..."
    cd $workdir
    rm ${tmpfile}*
    python ../getFiles.py ${ncode} ${lastUpdate} > ${tmpfile}.tex &&

        echo "LaTeX..." &&
        platex ${tmpfile}.tex >> ${texlog}&&
        platex ${tmpfile}.tex >> ${texlog}&&
        platex ${tmpfile}.tex >> ${texlog}&&
        dvipdfmx -q -p a5 ${tmpfile}.dvi >> ${texlog}&&
        mv -f ${tmpfile}.pdf ${fname}.pdf &&
        mv -f ${fname}.pdf ${savePath}
    if [ $? -ne 0 ];
    then
        echo "Skip \"${ncode}\""
        iupdate=${lastUpdate}
    else
        echo "Complete!"
    fi
    cd ../
    echo "${ncode},${fname},${iupdate}" >> ${target}${dummy}
done

mv ${target}${dummy} ${target}

exit 0
