# Pesquisa sobre a CSD130 (23/11/2026)

O que se achou fora do manual, com as fontes. “Fonte única” quer dizer que só um lugar confirma; o que não se achou
está no fim, para não procurar de novo.

## Funções do módulo

- **Sem atualização de firmware:** a página de suporte só tem os manuais em PDF
  (<https://www.carlsbro.com/support/>).
- **DRUM OFF:** tira a bateria da música demo, para tocar junto; o volume da bateria (“d”) e do acompanhamento (“A”)
  vão de 0 a 32, no SONG (manual, pág. 21).
- **START/STOP:** um toque toca a demo, dois tocam a gravação, três param (manual, pág. 21).
- **Local On/Off:** em SET UP aparece “Lon” ou “Lof”, e se troca com −DATA+. Em “Lof” os pads não tocam o som do
  módulo, só mandam a nota: serve para o modo computador sem o som dobrado (manual, págs. 23 e 27).
- **Reset de fábrica, passo completo:** ligar segurando TEMPO+ e SET UP, escolher “RELOAD FAC SET” e confirmar com
  SET UP (Melodics, fonte única: <https://support.melodics.com/en/articles/9861709-how-to-factory-reset-your-midi-instrument>).
- **Relógio MIDI:** a tabela da pág. 27 diz que o módulo manda o relógio, mas o texto da pág. 26 diz que a música e o
  metrônomo não são enviados. Medido em 23/11/2026: o metrônomo sozinho não manda relógio. Falta medir com a demo
  tocando.

## Pads

- **Pratos de 10" com abafamento (choke):** <https://mixdownmag.com.au/reviews/drums/carlsbro-csd130-electronic-drum-kit/>
  e <https://www.drumcentral.co.uk/carlsbro-csd130m-electronic-drum-kit/>.
- **CSD130M:** só a caixa é de malha (mesh), com duas zonas; o módulo “Commander 130M” tem os mesmos 250 sons e
  20 + 10 kits (<https://reverb.com/item/11267669-carlsbro-csd130m-mesh-snare-compact-electronic-drum-kit> e
  <https://www.scan.co.uk/products/carlsbro-csd130-m-digital-drum-kit-w-mesh-head-snare>).
- **Segundo prato de ataque:** o painel traseiro tem uma entrada só, o conector dos pads (manual, pág. 14); não se
  achou entrada para prato ou tom a mais.
- **Pedal duplo:** um comprador diz que não funciona (Bax, fonte única, não conferida).

## Modo computador no Linux

- **Hydrogen:** a opção “Use output note as input note” (Preferências, MIDI) é o `fixed_mapping` do `hydrogen.conf`
  (<https://github.com/hydrogen-music/hydrogen/blob/master/src/core/Preferences/Preferences.cpp>). Sem ela, a nota 36
  vai para a primeira peça do kit, a 37 para a segunda, e assim por diante. O `ferramentas/modo-computador.py` deixa
  as duas formas iguais.
- **DrumGizmo:** o mapa de notas é `<midimap><map note="38" instr="Snare"/></midimap>`, com o nome da peça do kit
  (<https://drumgizmo.org/wiki/doku.php?id=documentation:file_formats>); pela linha de comando,
  `drumgizmo -i jackmidi -I midimap=mapa.xml -o jackaudio kit.xml` (<https://drumgizmo.org/wiki/doku.php?id=cli-howto>).
- **Atraso do som:** com o PipeWire, `PIPEWIRE_LATENCY=128/48000` dá blocos de 2,7 ms. O teto mais citado por
  bateristas é de uns 10 ms no total (fóruns e lojas, não estudo:
  <https://www.toontrack.com/forums/topic/e-drummers-do-not-want-the-additional-latency-introduced-with-v3-4-1-plug-in/page/2>,
  <https://www.sweetwater.com/insync/?p=203100>).

## Kits de som livres

| Kit | Licença | Tamanho | Fonte |
|---|---|---|---|
| DRSKit (DrumGizmo) | CC-BY-4.0 | 2,8 GB | <https://drumgizmo.org/wiki/doku.php?id=kits:drskit> |
| CrocellKit (DrumGizmo) | CC-BY-4.0 | 5,5 GB | <https://drumgizmo.org/wiki/doku.php?id=kits:crocellkit> |
| The Aasimonster (DrumGizmo) | CC-BY-4.0 | 2,3 GB | <https://drumgizmo.org/wiki/doku.php?id=kits:the_aasimonster> |
| AVL Drumkits | CC-BY-SA-3.0 | ~96 MB (plugin LV2) | <https://www.bandshed.net/avldrumkits/> |
| Big Rusty, Swirly e Unruly Drums (Karoryfer) | CC0-1.0 | 1,6 a 2,3 GB | <https://sfzinstruments.github.io/drums> (fonte única) |
| Naked Drums (Wilkinson Audio) | CC-BY-4.0 | 1,3 GB | idem (fonte única) |
| Salamander Drumkit | CC-BY-SA-3.0 | ~370 MB | idem (fonte única) |

## Procurado e não achado

Tópicos da CSD130 no Reddit (r/edrums) e no VDrums; perguntas da Amazon, Thomann e Gear4music; combinações de botões
fora do manual; relatos de disparo duplo ou de defeito no pedal do chimbal; pads de outras marcas compatíveis;
medidas do atraso pelo USB.
