#!/usr/bin/env python3
"""Treino de tempo com a CSD130: grava pelo USB o que é tocado e mede o tempo e a força.

Uso:
    python3 ferramentas/treino.py                  # grava até Ctrl+C, depois mostra o relatório
    python3 ferramentas/treino.py --segundos 120   # grava 2 minutos
    python3 ferramentas/treino.py --grade 8        # compara com colcheias (o padrão é semicolcheia, 16)
    python3 ferramentas/treino.py --ver treinos/2026-11-23_015000.json   # relatório de um treino salvo
    python3 ferramentas/treino.py --historico      # uma linha por treino salvo

Com o metrônomo do módulo ligado, o módulo manda o relógio MIDI (manual, pág. 27), e cada batida é comparada com a
grade do metrônomo: o relógio e as batidas passam pelo mesmo USB, então o atraso do cabo se anula. Sem relógio, o
relatório mede só a regularidade entre as batidas (o andamento é estimado delas).

Lê o MIDI cru (/dev/snd/midiC*D0), sem biblioteca de fora. Os treinos ficam em treinos/, fora do git.
"""

import argparse
import json
import os
import select
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_TREINOS = RAIZ / "treinos"

# Notas que a CSD130 manda (docs/mapa-de-notas.md). Bumbo e pedal do chimbal ainda pelo GM, a conferir.
NOMES = {
    36: "bumbo",
    37: "aro",
    38: "caixa",
    43: "tom 3",
    44: "pedal do chimbal",
    45: "tom 2",
    46: "condução",
    48: "tom 1",
    49: "chimbal",
    51: "ataque",
}

RELOGIOS_POR_TEMPO = 24  # o relógio MIDI manda 24 pulsos por semínima
DUPLA_MS = 25  # a mesma nota de novo antes disso é disparo duplo do pad, não batida


class Leitor:
    """Transforma os bytes MIDI em eventos, com status corrido e mensagens de tempo real no meio."""

    def __init__(self):
        self.status = None
        self.dados = []

    def alimentar(self, bloco, t_ms):
        eventos = []
        for b in bloco:
            if b >= 0xF8:
                tipo = {0xF8: "relogio", 0xFA: "inicio", 0xFB: "continua", 0xFC: "parada"}.get(b)
                if tipo:
                    eventos.append({"t": t_ms, "tipo": tipo})
                continue
            if b >= 0xF0:
                self.status, self.dados = None, []
                continue
            if b & 0x80:
                self.status, self.dados = b, []
                continue
            if self.status is None:
                continue
            self.dados.append(b)
            precisa = 1 if (self.status & 0xF0) in (0xC0, 0xD0) else 2
            if len(self.dados) < precisa:
                continue
            if (self.status & 0xF0) == 0x90 and self.dados[1] > 0:
                eventos.append({"t": t_ms, "tipo": "nota", "nota": self.dados[0], "forca": self.dados[1]})
            self.dados = []
        return eventos


def achar_porta():
    try:
        cartoes = Path("/proc/asound/cards").read_text().splitlines()
    except OSError:
        cartoes = []
    for linha in cartoes:
        partes = linha.split()
        if partes and partes[0].isdigit() and "USB MIDI" in linha:
            return f"/dev/snd/midiC{partes[0]}D0"
    return None


def gravar(porta, segundos=None):
    leitor = Leitor()
    eventos = []
    fd = os.open(porta, os.O_RDONLY | os.O_NONBLOCK)
    t0 = time.monotonic_ns()
    print("Gravando. Ctrl+C para parar." if not segundos else f"Gravando por {segundos} s. Ctrl+C para parar antes.")
    try:
        while True:
            if segundos and time.monotonic_ns() - t0 > segundos * 1e9:
                break
            prontos, _, _ = select.select([fd], [], [], 0.2)
            if not prontos:
                continue
            bloco = os.read(fd, 512)
            t_ms = (time.monotonic_ns() - t0) / 1e6
            eventos += leitor.alimentar(bloco, t_ms)
    except KeyboardInterrupt:
        pass
    finally:
        os.close(fd)
    return eventos


def tirar_duplas(notas):
    limpas, duplas, ultima = [], 0, {}
    for n in notas:
        anterior = ultima.get(n["nota"])
        if anterior is not None and n["t"] - anterior < DUPLA_MS:
            duplas += 1
            continue
        ultima[n["nota"]] = n["t"]
        limpas.append(n)
    return limpas, duplas


def trechos_do_relogio(relogios):
    """Separa o relógio em trechos contínuos (o metrônomo parado e ligado de novo vira outro trecho)."""
    trechos, atual = [], []
    for t in relogios:
        if atual and t - atual[-1] > 500:
            trechos.append(atual)
            atual = []
        atual.append(t)
    if atual:
        trechos.append(atual)
    return [tr for tr in trechos if len(tr) >= 2 * RELOGIOS_POR_TEMPO]


def reta(ts):
    """Mínimos quadrados de t = a + b·k: a grade do metrônomo sem o tremor do USB."""
    n = len(ts)
    ks = range(n)
    mk, mt = (n - 1) / 2, sum(ts) / n
    b = sum((k - mk) * (t - mt) for k, t in zip(ks, ts)) / sum((k - mk) ** 2 for k in ks)
    return mt - b * mk, b


def analisar(eventos, grade=16):
    notas = [e for e in eventos if e["tipo"] == "nota"]
    notas, duplas = tirar_duplas(notas)
    relogios = [e["t"] for e in eventos if e["tipo"] == "relogio"]
    resultado = {"batidas": len(notas), "duplas": duplas, "grade": grade, "modo": "livre"}
    if notas:
        resultado["duracao_s"] = round((notas[-1]["t"] - notas[0]["t"]) / 1000, 1)

    trechos = trechos_do_relogio(relogios)
    passo = RELOGIOS_POR_TEMPO * 4 // grade
    medidas = []  # (nota, forca, desvio_ms, t)
    if trechos:
        resultado["modo"] = "metronomo"
        bpms = []
        for tr in trechos:
            a, b = reta(tr)
            bpms.append(60000 / (RELOGIOS_POR_TEMPO * b))
            inicio, fim = tr[0] - b * passo / 2, tr[-1] + b * passo / 2
            for n in notas:
                if not inicio <= n["t"] <= fim:
                    continue
                k = (n["t"] - a) / b
                alvo = round(k / passo) * passo
                medidas.append((n["nota"], n["forca"], n["t"] - (a + b * alvo), n["t"]))
        resultado["bpm"] = round(statistics.mean(bpms), 1)
        resultado["fora_do_metronomo"] = len(notas) - len(medidas)
    elif len(notas) >= 8:
        # Sem relógio: junta as batidas simultâneas (até 30 ms) e mede o intervalo entre elas.
        inicios = [notas[0]["t"]]
        for n in notas[1:]:
            if n["t"] - inicios[-1] > 30:
                inicios.append(n["t"])
        intervalos = [b - a for a, b in zip(inicios, inicios[1:])]
        mediana = statistics.median(intervalos)
        regulares = [i for i in intervalos if 0.6 * mediana <= i <= 1.4 * mediana]
        resultado["bpm_estimado"] = round(60000 / mediana, 1)
        resultado["intervalo_ms"] = round(mediana, 1)
        if len(regulares) >= 4:
            resultado["espalhamento_ms"] = round(statistics.pstdev(regulares), 1)
            terco = max(1, len(regulares) // 3)
            resultado["bpm_inicio"] = round(60000 / statistics.mean(regulares[:terco]), 1)
            resultado["bpm_fim"] = round(60000 / statistics.mean(regulares[-terco:]), 1)
        medidas = [(n["nota"], n["forca"], None, n["t"]) for n in notas]

    pecas = {}
    for nota, forca, desvio, _ in medidas:
        p = pecas.setdefault(nota, {"forcas": [], "desvios": []})
        p["forcas"].append(forca)
        if desvio is not None:
            p["desvios"].append(desvio)
    resultado["pecas"] = {}
    for nota in sorted(pecas, key=lambda x: -len(pecas[x]["forcas"])):
        p = pecas[nota]
        linha = {
            "nome": NOMES.get(nota, f"nota {nota}"),
            "batidas": len(p["forcas"]),
            "forca_media": round(statistics.mean(p["forcas"]), 1),
            "forca_variacao": round(statistics.pstdev(p["forcas"]), 1),
        }
        if p["desvios"]:
            linha["desvio_medio_ms"] = round(statistics.mean(p["desvios"]), 1)
            linha["espalhamento_ms"] = round(statistics.pstdev(p["desvios"]), 1)
        resultado["pecas"][str(nota)] = linha

    desvios = [d for _, _, d, _ in medidas if d is not None]
    if desvios:
        resultado["desvio_medio_ms"] = round(statistics.mean(desvios), 1)
        resultado["espalhamento_ms"] = round(statistics.pstdev(desvios), 1)
        quartos = [[] for _ in range(4)]
        t_ini, t_fim = medidas[0][3], medidas[-1][3]
        for _, _, d, t in medidas:
            i = min(3, int(4 * (t - t_ini) / max(1, t_fim - t_ini)))
            quartos[i].append(d)
        resultado["por_quarto_ms"] = [round(statistics.mean(q), 1) if q else None for q in quartos]
    return resultado


def nota_do_espalhamento(ms):
    # Referência prática para bateria, não norma: abaixo de 10 ms quase ninguém percebe.
    if ms < 10:
        return "excelente"
    if ms < 20:
        return "bom"
    if ms < 35:
        return "regular"
    return "a treinar"


def lado(ms):
    if abs(ms) < 5:
        return "em cima do tempo"
    return f"{'atrasa' if ms > 0 else 'adianta'} {abs(ms):.0f} ms"


def relatorio(r, quando=None):
    linhas = []
    cabeca = f"Treino{' de ' + quando if quando else ''}: {r['batidas']} batidas"
    if r.get("duracao_s"):
        cabeca += f" em {r['duracao_s']:.0f} s"
    linhas += [cabeca, ""]
    if not r["batidas"]:
        return "Nenhuma batida chegou. Conferir o cabo USB e se o módulo está ligado."

    if r["modo"] == "metronomo":
        nomes_grade = {4: "semínimas", 8: "colcheias", 16: "semicolcheias"}
        linhas.append(f"Metrônomo do módulo: {r['bpm']:.0f} BPM; grade de {nomes_grade.get(r['grade'], r['grade'])}.")
        linhas.append(
            f"No geral: {lado(r['desvio_medio_ms'])}; espalhamento de {r['espalhamento_ms']:.0f} ms "
            f"({nota_do_espalhamento(r['espalhamento_ms'])})."
        )
        q = r.get("por_quarto_ms")
        if q and all(v is not None for v in q):
            linhas.append("Ao longo do treino (do 1º ao 4º quarto): " + ", ".join(f"{v:+.0f} ms" for v in q) + ".")
            if q[3] - q[0] > 10:
                linhas.append("  → foi atrasando: o fim ficou mais atrás que o começo.")
            elif q[0] - q[3] > 10:
                linhas.append("  → foi correndo: o fim ficou mais à frente que o começo.")
        if r.get("fora_do_metronomo"):
            linhas.append(f"{r['fora_do_metronomo']} batidas fora do metrônomo (antes de ligar ou depois de parar).")
    else:
        linhas.append("Sem metrônomo (o módulo não mandou relógio): medida só a regularidade entre as batidas.")
        if "bpm_estimado" in r:
            linhas.append(f"Andamento estimado: {r['bpm_estimado']:.0f} BPM (um intervalo de {r['intervalo_ms']:.0f} ms).")
        if "espalhamento_ms" in r:
            linhas.append(
                f"Espalhamento dos intervalos: {r['espalhamento_ms']:.0f} ms ({nota_do_espalhamento(r['espalhamento_ms'])})."
            )
            linhas.append(f"Começo {r['bpm_inicio']:.0f} BPM, fim {r['bpm_fim']:.0f} BPM.")
    if r["duplas"]:
        linhas.append(f"{r['duplas']} disparos duplos descartados (o pad disparou duas vezes numa batida).")

    linhas += ["", "| Peça | Batidas | Tempo | Espalhamento | Força média | Variação da força |", "|---|---|---|---|---|---|"]
    for p in r["pecas"].values():
        tempo = lado(p["desvio_medio_ms"]) if "desvio_medio_ms" in p else "—"
        esp = f"{p['espalhamento_ms']:.0f} ms" if "espalhamento_ms" in p else "—"
        linhas.append(
            f"| {p['nome']} | {p['batidas']} | {tempo} | {esp} | {p['forca_media']:.0f} | ±{p['forca_variacao']:.0f} |"
        )
    return "\n".join(linhas)


def historico():
    arquivos = sorted(PASTA_TREINOS.glob("*.json"))
    if not arquivos:
        return "Nenhum treino salvo ainda."
    linhas = ["| Treino | Batidas | BPM | Tempo | Espalhamento |", "|---|---|---|---|---|"]
    for arq in arquivos:
        r = json.loads(arq.read_text())["resultado"]
        bpm = r.get("bpm") or r.get("bpm_estimado") or "—"
        tempo = lado(r["desvio_medio_ms"]) if "desvio_medio_ms" in r else "—"
        esp = f"{r['espalhamento_ms']:.0f} ms" if "espalhamento_ms" in r else "—"
        linhas.append(f"| {arq.stem} | {r['batidas']} | {bpm} | {tempo} | {esp} |")
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--segundos", type=float)
    ap.add_argument("--grade", type=int, default=16, choices=[4, 8, 16])
    ap.add_argument("--porta")
    ap.add_argument("--ver", type=Path, help="relatório de um treino salvo")
    ap.add_argument("--historico", action="store_true")
    args = ap.parse_args()

    if args.historico:
        print(historico())
        return
    if args.ver:
        dados = json.loads(args.ver.read_text())
        r = analisar(dados["eventos"], args.grade)
        print(relatorio(r, dados.get("quando")))
        return

    porta = args.porta or achar_porta()
    if not porta:
        sys.exit("A bateria não aparece no computador: conferir o cabo USB e se o módulo está ligado.")
    eventos = gravar(porta, args.segundos)
    quando = datetime.now().strftime("%d/%m/%Y %H:%M")
    r = analisar(eventos, args.grade)
    PASTA_TREINOS.mkdir(exist_ok=True)
    arquivo = PASTA_TREINOS / f"{datetime.now():%Y-%m-%d_%H%M%S}.json"
    arquivo.write_text(json.dumps({"quando": quando, "eventos": eventos, "resultado": r}, ensure_ascii=False))
    print()
    print(relatorio(r, quando))
    print(f"\nSalvo em {arquivo.relative_to(RAIZ)}.")


if __name__ == "__main__":
    main()
