# Mapa de notas da CSD130

A nota MIDI que cada pad manda pelo USB. Serve para o modo computador: o programa (DrumGizmo, Hydrogen) precisa
saber qual nota é qual peça.

Como preencher: `ferramentas/ler-pads.sh`, bater em cada pad e anotar a nota. Ler só com todos os pads já ligados:
uma ponta do cabo solta dispara nota ao ser tocada, e as notas parecem batidas de verdade (visto em 23/11/2026). O
manual não traz este mapa; a lista GM das págs. 36 e 37 é a do som que o módulo toca quando **recebe** cada nota, que
não é a que ele manda nos pratos. Para saber o som de um pad sem ouvir: VOICE VOL/PAN/TUN uma vez, bater no pad e ler
o número no visor (sem apertar −DATA+ nem SAVE).

| Pad | Nota que manda | Nota GM esperada | Conferido em |
|---|---|---|---|
| Bumbo | a conferir (a peça ainda não chegou) | 36 | |
| Caixa | 38 | 38 | 23/11/2026 |
| Aro da caixa | 37 | 37 | 23/11/2026 |
| Tom 1 | 48 | 48 | 23/11/2026 |
| Tom 2 | 45 | 45 | 23/11/2026 |
| Tom 3 | 43 | 43 | 23/11/2026 |
| Chimbal fechado | a conferir (sem o pedal) | 42 | |
| Chimbal | 49 | 46 | 23/11/2026 |
| Pedal do chimbal | a conferir (a peça ainda não chegou) | 44 | |
| Ataque | 51 | 49 | 23/11/2026 |
| Condução | 46 | 51 | 23/11/2026 |

Leitura de 23/11/2026, com a sensibilidade que o módulo tinha: os cinco pads de pele vão do fraco (36 a 56) ao
máximo (119 a 127), e os três pratos do fraco (26 a 40) ao forte (119 a 127).

**Os pratos não seguem o padrão GM.** O chimbal manda 49, o ataque 51 e a condução 46, com cada ponta do cabo na peça
da etiqueta. O som que o módulo toca está certo: no visor, o pad do chimbal mostra o som 071 (OHIHAT1), o do ataque
o 140 (SPLSH2) e o da condução o 135 (RIDESTD). Então só a nota que sai pelo USB é outra; no modo bateria nada muda,
e no modo computador o programa precisa deste mapa, e não do GM.

## Ajustes da bateria toda

| Ajuste | Valor | Por quê |
|---|---|---|
| Sensibilidade (01 a 08) | a conferir | |
| Crosstalk (01 a 16) | a conferir | |
| Curva (1 a 6) | a conferir | |
