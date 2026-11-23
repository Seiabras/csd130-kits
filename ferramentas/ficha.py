#!/usr/bin/env python3
"""Gera a ficha de digitação de um kit da Carlsbro CSD130 a partir do arquivo .toml.

Uso:
    python3 ferramentas/ficha.py kits/exemplo-rock.toml     # mostra a ficha
    python3 ferramentas/ficha.py --todas                     # grava fichas/<kit>.md de todos os kits

A ficha segue a ordem dos botões do módulo: SAVE e o número do USER, depois uma passada por pad para o som, outra
para o volume, outra para o pan e outra para a afinação, e o SAVE final. Os limites vêm do manual (págs. 19 e 20).
"""

import sys
import tomllib
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Os pads da CSD130, na ordem em que a ficha os lista (manual, págs. 3 a 10).
PADS = [
    ("kick", "Bumbo (kick)"),
    ("caixa", "Caixa (snare)"),
    ("tom1", "Tom 1"),
    ("tom2", "Tom 2"),
    ("tom3", "Tom 3 (surdo)"),
    ("chimbal", "Chimbal (hi-hat)"),
    ("ataque", "Prato de ataque (crash)"),
    ("conducao", "Prato de condução (ride)"),
]

LIMITES = {
    "som": (1, 250),
    "volume": (0, 32),
    "pan": (-8, 8),
    "afinacao": (-2, 2),
}

USER_MAX = 10  # o manual diz 10 na pág. 20 e 15 na pág. 28; 10 é o seguro até conferir no módulo


def carregar_sons():
    sons = {}
    for linha in (RAIZ / "dados" / "sons.tsv").read_text().splitlines()[1:]:
        numero, grupo, nome, _ = (linha.split("\t") + [""])[:4]
        sons[int(numero)] = f"{nome} ({grupo})"
    return sons


def validar(kit, arquivo):
    erros = []
    user = kit.get("user")
    if not isinstance(user, int) or not 1 <= user <= USER_MAX:
        erros.append(f"user deve ir de 1 a {USER_MAX}, veio {user!r}")
    pads = kit.get("pads", {})
    for chave, _ in PADS:
        pad = pads.get(chave)
        if pad is None:
            erros.append(f"falta o pad [pads.{chave}]")
            continue
        for campo, (menor, maior) in LIMITES.items():
            valor = pad.get(campo, 0 if campo in ("pan", "afinacao") else None)
            if not isinstance(valor, int) or not menor <= valor <= maior:
                erros.append(f"pads.{chave}.{campo} deve ir de {menor} a {maior}, veio {valor!r}")
    extras = set(pads) - {c for c, _ in PADS}
    if extras:
        erros.append(f"pads que a CSD130 não tem: {', '.join(sorted(extras))}")
    if erros:
        sys.exit(f"{arquivo}:\n  - " + "\n  - ".join(erros))


def sinal(valor):
    return f"+{valor}" if valor > 0 else str(valor)


def ficha(arquivo):
    kit = tomllib.loads(Path(arquivo).read_text())
    validar(kit, arquivo)
    sons = carregar_sons()
    pads = kit["pads"]
    user = kit["user"]
    linhas = [f"# Ficha: {kit.get('nome', Path(arquivo).stem)} (USER{user:02d})", ""]
    if kit.get("descricao"):
        linhas += [kit["descricao"], ""]
    if kit.get("referencias"):
        linhas += ["Músicas de referência: " + "; ".join(kit["referencias"]) + ".", ""]

    linhas += [
        "## Resumo",
        "",
        "| Pad | Som | Volume | Pan | Afinação |",
        "|---|---|---|---|---|",
    ]
    for chave, nome in PADS:
        p = pads[chave]
        som = f"{p['som']:03d} {sons.get(p['som'], '(nome a conferir)')}"
        linhas.append(
            f"| {nome} | {som} | {p['volume']} | {sinal(p.get('pan', 0))} | {sinal(p.get('afinacao', 0))} |"
        )
    linhas += ["", f"Reverb: {'ligado' if kit.get('reverb', False) else 'desligado'}.", ""]

    linhas += [
        "## Digitação no módulo",
        "",
        f"1. Apertar **KIT REV ON/OFF** até o kit, depois **SAVE**; com **−DATA+**, escolher **U{user:02d}** (o número "
        "pisca).",
        "2. **VOICE VOL/PAN/TUN** uma vez (som). Para cada pad: bater nele e acertar com **−DATA+**:",
    ]
    linhas += [f"   - {nome}: **{pads[c]['som']:03d}**" for c, nome in PADS]
    linhas.append("3. **VOICE VOL/PAN/TUN** de novo (aparece L, volume). Bater e acertar:")
    linhas += [f"   - {nome}: **{pads[c]['volume']}**" for c, nome in PADS]
    linhas.append("4. **VOICE VOL/PAN/TUN** de novo (aparece P, pan). Bater e acertar:")
    linhas += [f"   - {nome}: **{sinal(pads[c].get('pan', 0))}**" for c, nome in PADS]
    linhas.append("5. **VOICE VOL/PAN/TUN** de novo (aparece t, afinação). Bater e acertar:")
    linhas += [f"   - {nome}: **{sinal(pads[c].get('afinacao', 0))}**" for c, nome in PADS]
    linhas += [
        "6. **SAVE** para gravar (o número para de piscar). Trocar de kit ou faltar luz antes deste passo perde tudo.",
        f"7. Reverb **{'ligado' if kit.get('reverb', False) else 'desligado'}**: **KIT REV ON/OFF** até o reverb e "
        "acertar com **−DATA+**.",
        "",
    ]

    comp = kit.get("computador")
    if comp:
        linhas += ["## Modo computador", "", f"Kit: {comp.get('kit', 'a definir')}."]
        if comp.get("notas"):
            linhas.append(comp["notas"])
        linhas.append("")
    return "\n".join(linhas)


def main():
    if sys.argv[1:] == ["--todas"]:
        for arquivo in sorted((RAIZ / "kits").glob("*.toml")):
            if arquivo.stem == "modelo":
                continue
            destino = RAIZ / "fichas" / f"{arquivo.stem}.md"
            destino.write_text(ficha(arquivo))
            print(f"{destino.relative_to(RAIZ)}")
    elif len(sys.argv) == 2:
        print(ficha(sys.argv[1]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
