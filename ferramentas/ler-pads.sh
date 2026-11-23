#!/usr/bin/env bash
# Mostra, pad a pad, a nota MIDI e a força que a CSD130 manda pelo USB.
# Serve para montar o mapa de notas (docs/mapa-de-notas.md) e escolher sensibilidade e curva.
# Precisa do alsa-utils (aseqdump). Ctrl+C para sair.
set -euo pipefail

command -v aseqdump >/dev/null || { echo "Falta o aseqdump: instalar o pacote alsa-utils." >&2; exit 1; }

porta=$(aseqdump -l | awk 'NR>1 && $0 !~ /Through|System|PipeWire/ {print $1; exit}')
if [ -z "${porta:-}" ]; then
  echo "Nenhuma porta MIDI de bateria encontrada. Ligar o cabo USB e o módulo, e conferir com: aseqdump -l" >&2
  exit 1
fi

echo "Lendo a porta $porta. Bater em cada pad, um de cada vez, do mais fraco ao mais forte."
aseqdump -p "$porta" | awk '/Note on/ {
  for (i = 1; i <= NF; i++) { if ($i == "note") n = $(i+1); if ($i == "velocity") v = $(i+1) }
  gsub(",", "", n); printf "nota %3s  força %3s\n", n, v; fflush()
}
/Control change/ { print "controle: " $0; fflush() }'
