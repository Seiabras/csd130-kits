# csd130-kits

Kits para a bateria eletrônica **Carlsbro CSD130**, nos dois modos:

- **Modo bateria:** o som sai do próprio módulo, com os kits do usuário (USER01 a 10). Só bateria e amplificador,
  sem computador.
- **Modo computador:** o módulo manda as batidas pelo USB e o som sai de um sampler livre (DrumGizmo ou Hydrogen),
  com kits gravados de bateria acústica.

Cada kit é descrito uma vez, num arquivo `kits/*.toml`. Dele sai a ficha de digitação para o módulo, na ordem dos
botões, e a indicação do kit do computador. A CSD130 não aceita kit pelo USB (não tem System Exclusive), então a
ficha é também a cópia de segurança: o reset de fábrica apaga todos os kits do usuário.

## Como usar

Montar a ficha de um kit:

```bash
python3 ferramentas/ficha.py kits/exemplo-rock.toml
```

Gravar as fichas de todos os kits em `fichas/`:

```bash
python3 ferramentas/ficha.py --todas
```

Kit novo: copiar `kits/modelo.toml`, escolher os sons em `dados/sons.tsv` e gerar a ficha. O script confere os
limites do módulo (som 1 a 250, volume 0 a 32, pan −8 a +8, afinação −2 a +2, user 1 a 10).

Ler as notas que cada pad manda (precisa do `alsa-utils`):

```bash
ferramentas/ler-pads.sh
```

Baixar o kit do computador (DRSKit 2.1, cerca de 2,8 GB, fica em `sons/`, fora do git):

```bash
ferramentas/baixar-sons.sh
```

## O que tem aqui

| Caminho | O que é |
|---|---|
| `docs/csd130.md` | O que o módulo faz e não faz, com as páginas do manual |
| `docs/mapa-de-notas.md` | A nota MIDI de cada pad e os ajustes de sensibilidade |
| `dados/sons.tsv` | Os sons do módulo: número, grupo, nome e nota GM |
| `kits/` | Um arquivo por kit, e o `modelo.toml` |
| `fichas/` | As fichas geradas, para imprimir ou ler no celular |
| `ferramentas/` | O gerador de fichas, o leitor de pads e o baixador de sons |

`dados/sons.tsv` tem 208 dos 250 sons; os 42 que faltam (percussão e efeitos, entre o 170 e o 224) estão numa
página do manual que não sai como texto.

## Licenças

- Código (`ferramentas/`): MIT, ver `LICENSE`.
- Fichas, kits, mapas e textos: CC-BY-4.0, ver `LICENSE-CONTEUDO.md`.
- Os sons do modo computador não estão aqui. O DRSKit é da equipe do [DrumGizmo](https://drumgizmo.org), sob
  CC-BY-4.0, e o script baixa da página oficial.
- Carlsbro é marca do fabricante; este repositório não tem ligação com ele. O manual não está aqui.
