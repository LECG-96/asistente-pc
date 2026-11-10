import importlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import config


class CerebroTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        carpeta = cls.enterClassContext(tempfile.TemporaryDirectory())
        with patch.object(config, "BASE", Path(carpeta)):
            cls.cerebro = importlib.import_module("cerebro.intenciones")
        if cls.cerebro.aprendizaje.RUTA.parent.parent != Path(carpeta):
            raise RuntimeError("Las pruebas requieren una base de datos temporal.")
        cls.activacion = cls.cargar_activacion()

    @staticmethod
    def cargar_activacion():
        with patch("faster_whisper.WhisperModel"), patch("keyboard.add_hotkey"):
            return importlib.import_module("voz.activacion")

    def setUp(self):
        self.enterContext(patch.object(self.cerebro.ia, "RESPONDER_TODO", False))
        self.enterContext(patch.object(self.cerebro.ia, "conversacion_activa", return_value=False))
        self.cerebro.aprendizaje._sql("DELETE FROM comandos")

    def test_ordenes_negadas_no_ejecutan_acciones(self):
        with (
            patch("acciones.volumen._endpoint") as audio,
            patch("keyboard.send") as teclado,
            patch("acciones.energia._shutdown") as energia,
        ):
            for texto in (
                "Jarvis, no quiero silencio", "no quiero pausa", "mejor no subas el volumen",
                "por favor, no apagues el PC", "dije que no quiero pausa",
            ):
                with self.subTest(texto=texto):
                    self.assertIsNone(self.cerebro.procesar(texto))
            audio.assert_not_called()
            teclado.assert_not_called()
            energia.assert_not_called()

            self.cerebro.procesar("silencio")
            audio.return_value.SetMute.assert_called_once_with(1, None)
            self.cerebro.procesar("pausa")
            teclado.assert_called_once_with("play/pause media")

    def test_apagado_solicita_confirmacion_explicita(self):
        from acciones import energia
        from cerebro.confirmacion import Confirmacion, es_afirmativo

        with patch.object(energia, "_shutdown") as apagar:
            respuesta = self.cerebro.procesar("por favor apaga el PC")
            self.assertIsInstance(respuesta, Confirmacion)
            apagar.assert_not_called()
            for frase in ("Sí me escuchas", "sí, no", "sí 2", ""):
                self.assertFalse(es_afirmativo(frase))
            for frase in ("¡Sí!", "Confirmo.", "ok"):
                self.assertTrue(es_afirmativo(frase))

    def test_aprender_cerrar_conserva_la_confirmacion(self):
        from acciones import apps
        from cerebro.confirmacion import Confirmacion

        ficha = {"cerrar": "ejemplo.exe", "confirmar": True}
        with patch.dict(apps.APPS, {"ejemplo": ficha}, clear=True), patch.object(apps, "_terminar") as cerrar:
            self.cerebro.procesar("aprende cuando diga modo prueba cierra ejemplo")
            respuesta = self.cerebro.procesar("modo prueba")
            self.assertIsInstance(respuesta, Confirmacion)
            cerrar.assert_not_called()
            respuesta.accion()
            cerrar.assert_called_once_with("ejemplo.exe", False)

    def test_aprender_atajo_valida_y_ejecuta_las_teclas(self):
        with patch("keyboard.send") as teclado:
            self.cerebro.procesar("aprende cuando diga pestaña rápida presiona control t")
            teclado.assert_not_called()
            self.cerebro.procesar("pestaña rápida")
            teclado.assert_called_once_with("ctrl+t")
            respuesta = self.cerebro.procesar("aprende cuando diga otro comando presiona imposible")
            self.assertEqual(respuesta, "No entendí qué teclas presionar.")

    def test_respuestas_ya_guardadas_se_conservan(self):
        aprendizaje = self.cerebro.aprendizaje
        aprendizaje._sql("INSERT INTO comandos VALUES (?, ?, ?)", ("saludo", "responder", "hola"))
        self.assertEqual(self.cerebro.procesar("saludo"), "hola")

    def test_duracion_del_recordatorio_termina_antes_del_mensaje(self):
        from acciones.temporizadores import _extraer

        for frase, resultado in (
            ("avisame en 25 minutos que cocine dos horas", (1500, "cocine dos horas")),
            ("temporizador de una hora y media y cinco minutos", (5700, "")),
            ("temporizador de una hora 20 minutos", (4800, "")),
            ("avisame en media hora para descansar", (1800, "descansar")),
            ("temporizador", (0, "")),
        ):
            with self.subTest(frase=frase):
                self.assertEqual(_extraer(frase), resultado)

    def test_activacion_y_registro_sin_microfono(self):
        frases = {"jarvis": ["jarvis"], "rutina:prueba": ["vamos a estudiar"]}
        with (
            patch.object(self.activacion, "CLAVES", frases),
            patch.object(self.activacion, "normalizar_audio"),
            patch("builtins.print") as imprimir,
        ):
            for frase, resultado in (
                ("No digas vamos a estudiar", (None, "")),
                ("Vamos a estudiar.", ("rutina:prueba", "")),
                ("superjarvis, pausa", (None, "")),
                ("Jarvis, pausa", ("jarvis", "pausa")),
            ):
                self.activacion._modelo.transcribe.return_value = ([SimpleNamespace(text=frase)], None)
                self.assertEqual(self.activacion._detectar(None), resultado)
            imprimir.assert_not_called()
