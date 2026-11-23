#!/usr/bin/env python3
"""Modo computador: abre o Hydrogen com um kit preparado para as notas da CSD130 e liga a bateria nele.

Uso:
    python3 ferramentas/modo-computador.py           # prepara (se preciso), abre o Hydrogen e liga a bateria
    python3 ferramentas/modo-computador.py --preparar  # só prepara o kit e a configuração

O kit CSD130-GMRock é uma cópia do GMRockKit, que vem com o Hydrogen (GPL), com a nota de cada peça trocada para a
que a CSD130 manda (docs/mapa-de-notas.md): os pratos da CSD130 fogem do padrão GM. Nada disso vai para o git: o kit
e a configuração ficam em ~/.local/share/csd130-kits/hydrogen.

Precisa do pacote hydrogen, do alsa-utils (aconnect) e do PipeWire com o pw-jack (som de baixo atraso).
"""

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ORIGEM_KIT = Path("/usr/share/hydrogen/data/drumkits/GMRockKit")
CONF_PADRAO = Path("/usr/share/hydrogen/data/hydrogen.default.conf")
DADOS = Path.home() / ".local/share/csd130-kits/hydrogen"
NOME_KIT = "CSD130-GMRock"
QUANTUM = "128/48000"

# Peça do GMRockKit -> nota que a CSD130 manda. As que a bateria não tem ficam com a nota GM de sempre.
NOTAS = {
    "Kick": 36,
    "Stick": 37,  # aro da caixa
    "Snare": 38,
    "Tom 1": 48,
    "Tom 2": 45,
    "Floor Tom": 43,
    "Hat Open": 49,  # o pad do chimbal manda 49
    "Crash": 51,  # o pad do ataque manda 51
    "Ride": 46,  # o pad da condução manda 46
    "Hat Pedal": 44,
    "Hat Closed": 42,
    "Hand Clap": 39,
    "Snare Rimshot": 40,
    # Peças que a CSD130 não tem: nas posições livres (41, 47, 50) e depois do 51.
    "Ride 2": 41,
    "Bell": 47,
    "Splash": 50,
    "Cowbell": 56,
    "Hat Semi-Open": 82,
}


def preparar_kit():
    destino = DADOS / "drumkits" / NOME_KIT
    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(ORIGEM_KIT, destino)
    xml = destino / "drumkit.xml"
    texto = xml.read_text()
    texto = texto.replace("<name>GMRockKit</name>", f"<name>{NOME_KIT}</name>", 1)

    def trocar(m):
        bloco = m.group(0)
        nome = re.search(r"<name>([^<]*)</name>", bloco).group(1)
        if nome in NOTAS:
            bloco = re.sub(r"<midiOutNote>\d+</midiOutNote>", f"<midiOutNote>{NOTAS[nome]}</midiOutNote>", bloco)
        return bloco

    texto = re.sub(r"<instrument>.*?</instrument>", trocar, texto, flags=re.S)
    # O Hydrogen liga nota e peça pela nota de saída (fixed_mapping) ou pela posição na lista (nota - 36).
    # Pondo cada peça na posição da sua nota, os dois jeitos dão o mesmo resultado.
    blocos = re.findall(r"<instrument>.*?</instrument>", texto, flags=re.S)
    def nota(b):
        return int(re.search(r"<midiOutNote>(\d+)</midiOutNote>", b).group(1))
    ordem = sorted(blocos, key=lambda b: (nota(b) > 51, nota(b)))
    lista = re.search(r"(<instrumentList>)(.*)(</instrumentList>)", texto, flags=re.S)
    miolo = lista.group(2)
    primeiro, ultimo = miolo.index(blocos[0]), miolo.rindex(blocos[-1]) + len(blocos[-1])
    novo = miolo[:primeiro] + "\n".join(ordem) + miolo[ultimo:]
    texto = texto[: lista.start(2)] + novo + texto[lista.end(2) :]
    notas = re.findall(r"<midiOutNote>(\d+)</midiOutNote>", texto)
    if len(notas) != len(set(notas)):
        sys.exit(f"Duas peças com a mesma nota no kit: {sorted(notas)}")
    xml.write_text(texto)


def saida_de_som():
    """As duas entradas da placa de som no PipeWire (esquerda e direita)."""
    portas = subprocess.run(["pw-link", "-i"], capture_output=True, text=True).stdout.split()
    fl = next((p for p in portas if p.startswith("alsa_output") and p.endswith(":playback_FL")), None)
    fr = fl and fl.replace(":playback_FL", ":playback_FR")
    return fl, fr


def preparar_conf():
    conf = DADOS / "hydrogen.conf"
    texto = conf.read_text() if conf.exists() else CONF_PADRAO.read_text()
    fl, fr = saida_de_som()
    trocas = {
        r"<audio_driver>[^<]*</audio_driver>": "<audio_driver>JACK</audio_driver>",
        r"<samplerate>\d+</samplerate>": "<samplerate>48000</samplerate>",
        r"<fixed_mapping>\w+</fixed_mapping>": "<fixed_mapping>true</fixed_mapping>",  # nota de saída = de entrada
        # A CSD130 manda "soltou a nota" logo depois da batida; sem isto o Hydrogen corta o som.
        r"<ignore_note_off>\w+</ignore_note_off>": "<ignore_note_off>true</ignore_note_off>",
        r"<driverName>[^<]*</driverName>": "<driverName>ALSA</driverName>",
        r"<jack_connect_defaults>\w+</jack_connect_defaults>": "<jack_connect_defaults>true</jack_connect_defaults>",
        r"<restoreLastSong>\w+</restoreLastSong>": "<restoreLastSong>false</restoreLastSong>",
    }
    if fl:
        trocas[r"<jack_port_name_1>[^<]*</jack_port_name_1>"] = f"<jack_port_name_1>{fl}</jack_port_name_1>"
        trocas[r"<jack_port_name_2>[^<]*</jack_port_name_2>"] = f"<jack_port_name_2>{fr}</jack_port_name_2>"
    for padrao, novo in trocas.items():
        texto, n = re.subn(padrao, novo, texto, count=1)
        if not n:
            sys.exit(f"Não achei {padrao} na configuração padrão do Hydrogen.")
    conf.write_text(texto)
    return conf


def porta(nome):
    saida = subprocess.run(["aconnect", "-l"], capture_output=True, text=True).stdout
    m = re.search(rf"client (\d+): '{re.escape(nome)}", saida)
    return m.group(1) if m else None


def main():
    if not ORIGEM_KIT.exists():
        sys.exit("Falta o Hydrogen: instalar o pacote hydrogen.")
    DADOS.mkdir(parents=True, exist_ok=True)
    preparar_kit()
    conf = preparar_conf()
    if "--preparar" in sys.argv:
        print(f"Kit e configuração prontos em {DADOS}.")
        return

    bateria = porta("USB MIDI")
    if not bateria:
        sys.exit("A bateria não aparece: conferir o cabo USB e se o módulo está ligado.")
    subprocess.run(["pkill", "-x", "hydrogen"], check=False)
    time.sleep(1)
    # Bloco de 128 amostras a 48 kHz: 2,7 ms (o padrão do PipeWire aqui é 1024, 21 ms).
    ambiente = dict(os.environ, PIPEWIRE_QUANTUM=QUANTUM, PIPEWIRE_LATENCY=QUANTUM)
    subprocess.Popen(
        ["pw-jack", "hydrogen", "-d", "JACK", "--user-data", str(DADOS), "--config", str(conf), "-k", NOME_KIT,
         "-V", "Info", "-L", str(DADOS / "hydrogen.log")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env=ambiente,
    )
    for _ in range(40):
        time.sleep(0.5)
        h2 = porta("Hydrogen")
        if h2:
            subprocess.run(["aconnect", f"{bateria}:0", f"{h2}:0"], check=False)
            print(f"Hydrogen aberto com o kit {NOME_KIT}, e a bateria ligada nele. Pode tocar.")
            return
    sys.exit("O Hydrogen abriu, mas a porta MIDI dele não apareceu: em Preferências > MIDI, escolher ALSA.")


if __name__ == "__main__":
    main()
