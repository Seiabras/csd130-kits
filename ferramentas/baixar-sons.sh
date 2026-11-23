#!/usr/bin/env bash
# Baixa o DRSKit 2.1 do DrumGizmo para sons/ (fora do git). São cerca de 2,8 GB.
# Licença do kit: Creative Commons Attribution 4.0 (CC-BY-4.0), da equipe do DrumGizmo.
# Página oficial: https://drumgizmo.org/wiki/doku.php?id=kits:drskit
set -euo pipefail

raiz=$(cd "$(dirname "$0")/.." && pwd)
destino="$raiz/sons"
url="https://drumgizmo.org/kits/DRSKit/DRSKit2_1.zip"
mkdir -p "$destino"

if [ -d "$destino/DRSKit" ]; then
  echo "O DRSKit já está em $destino/DRSKit."
  exit 0
fi

read -r -p "Baixar o DRSKit 2.1 (cerca de 2,8 GB) para $destino? [s/N] " resposta
[ "$resposta" = "s" ] || [ "$resposta" = "S" ] || { echo "Nada baixado."; exit 0; }

curl -L --fail -C - -o "$destino/DRSKit2_1.zip" "$url"
unzip -q "$destino/DRSKit2_1.zip" -d "$destino"
rm "$destino/DRSKit2_1.zip"
echo "Pronto. No DrumGizmo, abrir o arquivo .xml do kit dentro de $destino."
echo "Crédito: DRSKit, equipe do DrumGizmo, CC-BY-4.0."
