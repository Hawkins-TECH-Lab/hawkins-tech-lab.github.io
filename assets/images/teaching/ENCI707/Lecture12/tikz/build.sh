#!/usr/bin/env bash
# Compile every TikZ source in this folder to ../<name>.svg (and ../<name>.pdf for Beamer/print).
# Requires pdflatex and pdftocairo (both ship with TeX Live).
set -euo pipefail
cd "$(dirname "$0")"
for tex in *.tex; do
  name="${tex%.tex}"
  pdflatex -interaction=nonstopmode -halt-on-error "$tex" > /dev/null
  mv "$name.pdf" ..
  pdftocairo -svg "../$name.pdf" "../$name.svg"
  rm -f "$name.aux" "$name.log"
  echo "built $name"
done
