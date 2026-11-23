"""Testes do treino de tempo: python3 -m unittest discover testes"""

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ferramentas"))
import treino  # noqa: E402


def metronomo(bpm, tempos, tremor=0.0, semente=1):
    """Relógio MIDI de um metrônomo a `bpm`, por `tempos` semínimas, com tremor de USB em ms."""
    rnd = random.Random(semente)
    periodo = 60000 / bpm / 24
    return [{"t": k * periodo + rnd.uniform(-tremor, tremor), "tipo": "relogio"} for k in range(24 * tempos)]


class TestLeitor(unittest.TestCase):
    def test_status_corrido_e_tempo_real_no_meio(self):
        leitor = treino.Leitor()
        # nota 38 força 100; relógio no meio da mensagem; status corrido: nota 48 força 50; nota 48 força 0 (solta)
        ev = leitor.alimentar(bytes([0x99, 38, 0xF8, 100, 48, 50, 48, 0]), 10.0)
        self.assertEqual([e["tipo"] for e in ev], ["relogio", "nota", "nota"])
        self.assertEqual((ev[1]["nota"], ev[1]["forca"]), (38, 100))
        self.assertEqual((ev[2]["nota"], ev[2]["forca"]), (48, 50))

    def test_mensagem_partida_em_dois_blocos(self):
        leitor = treino.Leitor()
        self.assertEqual(leitor.alimentar(bytes([0x99, 38]), 1.0), [])
        ev = leitor.alimentar(bytes([90]), 2.0)
        self.assertEqual((ev[0]["nota"], ev[0]["forca"], ev[0]["t"]), (38, 90, 2.0))

    def test_ignora_nota_solta_e_controle(self):
        leitor = treino.Leitor()
        ev = leitor.alimentar(bytes([0x89, 38, 64, 0xB9, 4, 127, 0xFA, 0xFC]), 0.0)
        self.assertEqual([e["tipo"] for e in ev], ["inicio", "parada"])


class TestAnalise(unittest.TestCase):
    def test_atraso_constante_com_metronomo(self):
        bpm = 100
        eventos = metronomo(bpm, 32, tremor=1.0)
        semicolcheia = 60000 / bpm / 4
        for i in range(8, 100):
            eventos.append({"t": i * semicolcheia + 12, "tipo": "nota", "nota": 38, "forca": 90})
        eventos.sort(key=lambda e: e["t"])
        r = treino.analisar(eventos, 16)
        self.assertEqual(r["modo"], "metronomo")
        self.assertAlmostEqual(r["bpm"], bpm, delta=0.5)
        self.assertAlmostEqual(r["desvio_medio_ms"], 12, delta=1)
        self.assertLess(r["espalhamento_ms"], 1)
        self.assertEqual(r["pecas"]["38"]["nome"], "caixa")

    def test_vai_atrasando(self):
        bpm = 90
        eventos = metronomo(bpm, 40)
        seminima = 60000 / bpm
        for i in range(2, 38):
            eventos.append({"t": i * seminima + i * 0.8, "tipo": "nota", "nota": 49, "forca": 70})
        eventos.sort(key=lambda e: e["t"])
        r = treino.analisar(eventos, 4)
        q = r["por_quarto_ms"]
        self.assertGreater(q[3] - q[0], 10)
        self.assertIn("foi atrasando", treino.relatorio(r))

    def test_disparo_duplo_descartado(self):
        eventos = metronomo(120, 16)
        eventos += [
            {"t": 500.0, "tipo": "nota", "nota": 38, "forca": 100},
            {"t": 510.0, "tipo": "nota", "nota": 38, "forca": 40},
            {"t": 1000.0, "tipo": "nota", "nota": 38, "forca": 100},
        ]
        eventos.sort(key=lambda e: e["t"])
        r = treino.analisar(eventos, 16)
        self.assertEqual((r["batidas"], r["duplas"]), (2, 1))

    def test_sem_relogio_estima_o_andamento(self):
        eventos = [{"t": i * 600.0, "tipo": "nota", "nota": 38, "forca": 80} for i in range(20)]
        r = treino.analisar(eventos, 16)
        self.assertEqual(r["modo"], "livre")
        self.assertAlmostEqual(r["bpm_estimado"], 100, delta=0.5)
        self.assertLess(r["espalhamento_ms"], 1)

    def test_sem_batidas(self):
        r = treino.analisar([], 16)
        self.assertIn("Nenhuma batida", treino.relatorio(r))


if __name__ == "__main__":
    unittest.main()
