DIRECTORY=/app/dict.csv
if [ -d "$DIRECTORY" ]; then
    /app/.linuxbrew/Cellar/mecab/0.996/libexec/mecab/mecab-dict-index -d /app/.linuxbrew/lib/mecab/dic/ipadic -u original.dic -f utf-8 -t utf-8 dict.csv
fi
