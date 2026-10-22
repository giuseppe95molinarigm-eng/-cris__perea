#!/bin/bash
# usage: render.sh [print]
set -e
cd "$(dirname "$0")"
python3 -I build.py $1
F=out/manual${1:+_print}.html
CH=/opt/pw-browsers/chromium-1194/chrome-linux/chrome
$CH --headless --no-sandbox --disable-gpu --no-pdf-header-footer --virtual-time-budget=20000 --run-all-compositor-stages-before-draw --print-to-pdf=${F%.html}.pdf file://$PWD/$F 2>/dev/null
$CH --headless --no-sandbox --disable-gpu --virtual-time-budget=20000 --window-size=900,1200 --dump-dom file://$PWD/$F 2>/dev/null | grep -o 'body class="[^"]*" data-overflow="[^"]*"'
pdfinfo ${F%.html}.pdf | grep -E "Pages|Page size"
