"""
EZPack AI CLI - Universal Edition
==================================
Combina todas las versiones de EZPack AI en un solo CLI:
  - Classic (Amigable / Mate / Experta / Omni / Meme)
  - CODE       (generadores procedurales -> Python)
  - KIDS       (adivinanzas infantiles)
  - LIVE       (voz + asistente en tiempo real)
  - PICTURES   (arte ASCII procedural)
  - QUESTIONS  (70 Q&A de Naturaleza, Tecnología y Biotec)
  - RAP        (generador de rap con estilos)
  - LOVE       (contención y empatía)

Ejecución:
    python ezpack_cli.py
    python ezpack_cli.py --modo mate
    python ezpack_cli.py --no-color

Python 3.11+  |  Solo stdlib.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import shutil
import sys
import textwrap
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional, Any

APP_NAME = "EZPack AI CLI"
APP_VERSION = "1.0.0"
APP_DIR = Path.home() / ".ezpack_ai"
DATA_FILE = APP_DIR / "data.json"
HISTORY_FILE = APP_DIR / "history.json"


# =========================================================================== #
# COLORES ANSI                                                                #
# =========================================================================== #
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    GRAY = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

    BG_PURPLE = "\033[45m"
    BG_BLUE = "\033[44m"

    @classmethod
    def disable(cls) -> None:
        for name in dir(cls):
            if not name.startswith("_") and isinstance(getattr(cls, name), str):
                setattr(cls, name, "")


# =========================================================================== #
# UTILIDADES                                                                  #
# =========================================================================== #
def ensure_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)


def now() -> datetime:
    return datetime.now()


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return default


def save_json(path: Path, data: Any) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError:
        pass


def wrap_text(text: str, width: int = 78, indent: str = "  ") -> str:
    lineas = []
    for parrafo in text.split("\n"):
        if not parrafo.strip():
            lineas.append("")
            continue
        wrapped = textwrap.wrap(parrafo, width=width, initial_indent=indent,
                                 subsequent_indent=indent)
        lineas.extend(wrapped)
    return "\n".join(lineas)


def strip_ansi(text: str) -> str:
    return re.sub(r"\033\[[0-9;]*m", "", text)


def typewriter(text: str, delay: float = 0.008, color: str = "") -> None:
    """Imprime texto carácter por carácter (efecto máquina de escribir)."""
    for ch in text:
        sys.stdout.write(color + ch + (C.RESET if color else ""))
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")


def input_prompt(prompt: str = "Tú > ") -> str:
    try:
        return input(f"\n{C.BRIGHT_CYAN}{prompt}{C.RESET}").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "salir"


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def term_width() -> int:
    try:
        return shutil.get_terminal_size().columns
    except OSError:
        return 80


# =========================================================================== #
# EVALUADOR MATEMÁTICO SEGURO                                                 #
# =========================================================================== #
FUNCIONES_MATH = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "log": math.log, "ln": math.log, "log10": math.log10, "log2": math.log2,
    "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
    "exp": math.exp, "factorial": math.factorial, "pow": pow,
}
CONSTANTES_MATH = {"pi": math.pi, "e": math.e, "tau": math.tau}


def tokenizar(expr: str) -> list:
    s = (expr.replace(",", ".").lower()
         .replace("×", "*").replace("÷", "/").replace("π", "pi")
         .replace("^", "**"))
    tokens: list = []
    i = 0
    while i < len(s):
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit() or c == ".":
            num = ""
            while i < len(s) and (s[i].isdigit() or s[i] == "."):
                num += s[i]
                i += 1
            tokens.append(("num", float(num)))
            continue
        if c in "+-*/%()":
            tokens.append((c, c))
            i += 1
            continue
        # Funciones y constantes
        matched = False
        for name in sorted(list(FUNCIONES_MATH) + list(CONSTANTES_MATH),
                            key=len, reverse=True):
            if s[i:i+len(name)] == name:
                sig = s[i+len(name)] if i + len(name) < len(s) else ""
                if not sig.isalpha():
                    tipo = "func" if name in FUNCIONES_MATH else "const"
                    tokens.append((tipo, name))
                    i += len(name)
                    matched = True
                    break
        if matched:
            continue
        if s[i:i+2] == "**":
            tokens.append(("**", "**"))
            i += 2
            continue
        raise ValueError(f"Carácter no permitido: {c}")
    # Re-convertir ** que quedó pegado a un solo *
    return tokens


def calcular(expresion: str) -> float:
    """Evalúa una expresión matemática de forma segura (sin eval)."""
    tokens = tokenizar(expresion)
    if not tokens:
        raise ValueError("Expresión vacía")

    pos = 0

    def peek():
        nonlocal pos
        return tokens[pos] if pos < len(tokens) else None

    def next_tok():
        nonlocal pos
        t = tokens[pos]
        pos += 1
        return t

    def parse_expr():
        left = parse_term()
        while peek() and peek()[0] in ("+", "-"):
            op = next_tok()[0]
            right = parse_term()
            left = left + right if op == "+" else left - right
        return left

    def parse_term():
        left = parse_factor()
        while peek() and peek()[0] in ("*", "/", "%"):
            op = next_tok()[0]
            right = parse_factor()
            if op == "*":
                left *= right
            elif op == "/":
                if right == 0:
                    raise ValueError("División entre cero")
                left /= right
            else:
                left %= right
        return left

    def parse_factor():
        base = parse_unary()
        if peek() and peek()[0] == "**":
            next_tok()
            exp = parse_factor()
            base = base ** exp
        return base

    def parse_unary():
        if peek() and peek()[0] == "-":
            next_tok()
            return -parse_unary()
        if peek() and peek()[0] == "+":
            next_tok()
            return parse_unary()
        return parse_primary()

    def parse_primary():
        t = peek()
        if not t:
            raise ValueError("Expresión incompleta")
        if t[0] == "(":
            next_tok()
            v = parse_expr()
            if not peek() or peek()[0] != ")":
                raise ValueError("Falta paréntesis de cierre")
            next_tok()
            return v
        if t[0] == "func":
            fn = next_tok()[1]
            if not peek() or peek()[0] != "(":
                raise ValueError(f"Se esperaba '(' después de {fn}")
            next_tok()
            v = parse_expr()
            if not peek() or peek()[0] != ")":
                raise ValueError(f"Falta paréntesis en {fn}")
            next_tok()
            return FUNCIONES_MATH[fn](v)
        if t[0] == "const":
            next_tok()
            return CONSTANTES_MATH[t[1]]
        if t[0] == "num":
            next_tok()
            return t[1]
        raise ValueError("Token inesperado")

    resultado = parse_expr()
    if pos != len(tokens):
        raise ValueError("Sobran símbolos en la expresión")
    if not isinstance(resultado, (int, float)) or not math.isfinite(resultado):
        raise ValueError("Resultado inválido")
    return round(resultado, 10)


# =========================================================================== #
# BASES DE DATOS                                                              #
# =========================================================================== #
CHISTES = [
    "¿Por qué los pájaros no usan Facebook? Porque ya tienen Twitter. 🐦",
    "¿Qué le dijo un semáforo a otro? No me mires que me estoy cambiando. 🚦",
    "¿Cómo se llama el campeón de buceo japonés? Tokofondo. 🤿",
    "¿Qué hace una abeja en el gimnasio? Zum-ba. 🐝",
    "—¿Cuál es tu libro favorito? —El de la biblioteca, porque tiene muchos tomos. 📚",
    "¿Qué le dijo una pared a la otra? Nos vemos en la esquina. 🧱",
    "—Doctor, me duele aquí. —Pues no se toque ahí. 🩺",
    "¿Cómo se despiden los químicos? Ácido un placer. 🧪",
    "¿Por qué el libro de matemáticas se suicidó? Porque tenía demasiados problemas. 📐",
    "¿Qué le dice un espagueti a otro? ¡El cuerpo me pide salsa! 🍝",
]

ADIVINANZAS_ANIMALES = [
    {
        "pregunta": "Tengo orejas largas y una cola chiquita. Salto y salto, y las zanahorias me encantan. ¿Quién soy?",
        "respuestas": ["conejo", "el conejo", "un conejo"],
        "nombre": "el Conejo 🐇",
        "pista": "Le encanta saltar y comer zanahorias."
    },
    {
        "pregunta": "Soy alta y amarilla, con manchas marrones y un cuello muy, muy largo. ¿Quién soy?",
        "respuestas": ["jirafa", "la jirafa", "una jirafa"],
        "nombre": "la Jirafa 🦒",
        "pista": "Tiene el cuello más largo del mundo."
    },
    {
        "pregunta": "Soy el rey de la selva, tengo una gran melena y cuando rugo todos me escuchan. ¿Quién soy?",
        "respuestas": ["leon", "león", "el leon", "el león"],
        "nombre": "el León 🦁",
        "pista": "Es el rey de la selva y hace ¡ROAAAR!"
    },
    {
        "pregunta": "Llevo mi casita en la espalda, camino muy despacito y me escondo cuando me asusto. ¿Quién soy?",
        "respuestas": ["tortuga", "la tortuga", "una tortuga"],
        "nombre": "la Tortuga 🐢",
        "pista": "Camina súper lento y tiene un caparazón duro."
    },
    {
        "pregunta": "Vivo en el agua, tengo 8 brazos largos y suelto tinta negra para esconderme. ¿Quién soy?",
        "respuestas": ["pulpo", "el pulpo", "un pulpo"],
        "nombre": "el Pulpo 🐙",
        "pista": "Tiene 8 tentáculos y vive en el mar."
    },
    {
        "pregunta": "Soy verde, me encanta saltar en los charcos y digo ¡croac, croac! ¿Quién soy?",
        "respuestas": ["rana", "la rana", "sapo", "el sapo"],
        "nombre": "la Rana 🐸",
        "pista": "Es verde y dice ¡Croac, croac!"
    },
    {
        "pregunta": "Tengo una trompa gigante, orejas enormes y soy el animal terrestre más grande. ¿Quién soy?",
        "respuestas": ["elefante", "el elefante", "un elefante"],
        "nombre": "el Elefante 🐘",
        "pista": "Es enorme, gris y usa su trompa para tomar agua."
    },
    {
        "pregunta": "Me gusta saltar de árbol en árbol, comer plátanos y hacer caras divertidas. ¿Quién soy?",
        "respuestas": ["mono", "el mono", "un mono", "chango"],
        "nombre": "el Mono 🐒",
        "pista": "Le encantan los plátanos y colgarse de las ramas."
    },
]

PREGUNTAS_QA = [
    ("nat", "¿Cómo producen oxígeno los árboles?",
     "A través de la fotosíntesis: convierten agua y dióxido de carbono en glucosa y oxígeno utilizando la luz solar como energía."),
    ("nat", "¿Qué causa las auroras boreales?",
     "Partículas cargadas del Sol colisionan con gases en la atmósfera terrestre, liberando luz en los polos."),
    ("nat", "¿Por qué el mar es salado?",
     "El agua de lluvia disuelve minerales y sales de las rocas terrestres y los transporta a los océanos mediante los ríos."),
    ("nat", "¿Qué es la bioluminiscencia?",
     "La capacidad de organismos vivos de producir luz mediante reacciones químicas internas, como las luciérnagas o medusas."),
    ("nat", "¿Cómo detectan los murciélagos a sus presas?",
     "Utilizan la ecolocalización: emiten ondas de ultrasonido que rebotan en los objetos para crear un mapa mental de su entorno."),
    ("nat", "¿Por qué cambian de color las hojas en otoño?",
     "Los árboles reducen la clorofila al bajar las horas de luz, dejando al descubierto otros pigmentos como carotenoides."),
    ("nat", "¿Qué determina el color de los ojos humanos?",
     "La cantidad y distribución de melanina en el iris, determinado por múltiples genes."),
    ("nat", "¿Cómo se forman los rayos?",
     "Por la acumulación de cargas eléctricas opuestas entre la nube y la tierra o entre nubes dentro de una tormenta."),
    ("nat", "¿Por qué los gatos ven mejor en la oscuridad?",
     "Tienen una capa reflectante detrás de la retina llamada 'tapetum lucidum' y más fotorreceptores tipo bastón."),
    ("nat", "¿Qué es la micorriza?",
     "Una relación simbiótica entre hongos y raíces de plantas donde intercambian agua y nutrientes por carbohidratos."),
    ("nat", "¿Por qué vuelan los pájaros en formación de 'V'?",
     "Ahorran energía aprovechando las corrientes de aire ascendentes generadas por las alas del ave delantera."),
    ("nat", "¿Qué produce los terremotos?",
     "La liberación repentina de energía acumulada en las fallas geológicas debido al movimiento de las placas tectónicas."),
    ("nat", "¿Cómo hibernan los osos?",
     "Reducen su ritmo cardíaco, temperatura corporal y metabolismo durante meses para sobrevivir al invierno con su grasa."),
    ("nat", "¿Qué es el ciclo del agua?",
     "El proceso continuo de evaporación, condensación, precipitación y escorrentía del agua en el planeta."),
    ("nat", "¿Cómo regenera sus extremidades la salamandra?",
     "Forma un blastema: un grupo de células madre capaces de dividirse y diferenciarse en hueso, músculo y piel."),
    ("nat", "¿Qué es la capa de ozono?",
     "Una capa de moléculas O3 en la estratosfera que absorbe la mayor parte de la radiación ultravioleta dañina del Sol."),
    ("nat", "¿Por qué ronronean los gatos?",
     "Para comunicar calma, autorregular el estrés o estimular la curación ósea y muscular con la frecuencia de la vibración."),
    ("nat", "¿Cómo funcionan las corrientes oceánicas?",
     "Son impulsadas por el viento, la rotación terrestre (Efecto Coriolis) y diferencias de densidad por salinidad y temperatura."),
    ("nat", "¿Por qué el cielo es azul?",
     "Por la dispersión de Rayleigh: la atmósfera dispersa las longitudes de onda cortas de la luz solar más que las largas."),
    ("nat", "¿Qué es una especie clave?",
     "Un organismo que ejerce un papel desproporcionadamente grande en mantener la estructura y equilibrio de un ecosistema."),
    ("tec", "¿Qué es una Red Neuronal Artificial?",
     "Un modelo computacional inspirado en el cerebro humano que aprende a identificar patrones a partir de grandes volúmenes de datos."),
    ("tec", "¿Cómo funciona la computación cuántica?",
     "Utiliza qubits que aprovechan la superposición y el entrelazamiento cuántico para procesar combinaciones masivas en paralelo."),
    ("tec", "¿Qué es Blockchain?",
     "Un libro mayor digital descentralizado e inmutable donde las transacciones se agrupan en bloques enlazados criptográficamente."),
    ("tec", "¿Cómo funciona la fibra óptica?",
     "Transmite datos en forma de pulsos de luz mediante reflexión interna total a través de hilos de vidrio o plástico."),
    ("tec", "¿Qué es la memoria RAM?",
     "Memoria de acceso aleatorio y volátil usada por la CPU para almacenar datos de acceso rápido de programas en ejecución."),
    ("tec", "¿Diferencia entre SSD y HDD?",
     "Un HDD usa platos magnéticos giratorios mecánicos; un SSD usa chips de memoria flash NAND sin partes móviles."),
    ("tec", "¿Qué es la arquitectura ARM?",
     "Una arquitectura de procesador RISC optimizada para bajo consumo de energía, dominante en smartphones y portátiles."),
    ("tec", "¿Qué es el Machine Learning?",
     "Una rama de la IA que permite a los sistemas aprender y mejorar a partir de datos sin ser programados explícitamente."),
    ("tec", "¿Cómo funciona el GPS?",
     "Triangula la posición midiendo el tiempo que tardan las señales enviadas por al menos cuatro satélites en llegar."),
    ("tec", "¿Qué es un protocolo API?",
     "Una interfaz de programación de aplicaciones que define las reglas para que diferentes programas se comuniquen entre sí."),
    ("tec", "¿Qué es la nube (Cloud Computing)?",
     "El acceso bajo demanda a servicios de computación (servidores, almacenamiento, BD) a través de Internet."),
    ("tec", "¿Cómo funciona la encriptación AES-256?",
     "Aplica rondas de sustitución y permutación de bits usando una clave de 256 bits casi imposible de romper por fuerza bruta."),
    ("tec", "¿Qué es el código abierto (Open Source)?",
     "Software cuyo código fuente es público para que cualquiera pueda inspeccionarlo, modificarlo y redistribuirlo."),
    ("tec", "¿Qué es la latencia de red?",
     "El tiempo de retardo que tarda un paquete de datos en viajar desde su origen hasta su destino a través de la red."),
    ("tec", "¿Cómo funciona un Transistor?",
     "Un conmutador semiconductor microscópico que controla o amplifica el flujo de corriente eléctrica en un circuito."),
    ("tec", "¿Qué es IoT (Internet de las Cosas)?",
     "La red de objetos físicos equipados con sensores y software para conectar e intercambiar datos por Internet."),
    ("tec", "¿Qué es la WebAssembly (Wasm)?",
     "Un formato de código binario portable que permite ejecutar código compilado a velocidad cercana a nativo en navegadores."),
    ("tec", "¿Cómo funciona la tecnología LiDAR?",
     "Mide distancias emitiendo pulsos de luz láser y calculando el tiempo de retorno para crear mapas 3D del entorno."),
    ("tec", "¿Qué es Docker y los contenedores?",
     "Empaqueta una aplicación con todas sus dependencias para ejecutarse de forma aislada y consistente en cualquier sistema."),
    ("tec", "¿Qué es la frecuencia de refresco (Hz)?",
     "El número de veces por segundo que una pantalla actualiza la imagen mostrada."),
    ("tec", "¿Qué es la Ley de Moore?",
     "La observación empírica de que el número de transistores en un microchip se duplica cada dos años aproximadamente."),
    ("tec", "¿Cómo funciona el procesamiento paralelo?",
     "Ejecuta múltiples tareas o hilos simultáneamente dividiendo el problema entre varios núcleos de CPU/GPU."),
    ("tec", "¿Qué es un Kernel de sistema operativo?",
     "El núcleo del sistema que gestiona la comunicación directa entre el hardware y el software de la computadora."),
    ("tec", "¿Qué es la visión por computadora?",
     "Campo de la IA dedicado a entrenar máquinas para interpretar y extraer información útil de imágenes digitales y video."),
    ("tec", "¿Cómo funciona una GPU?",
     "Procesador con miles de núcleos pequeños diseñados para realizar operaciones matemáticas paralelas hiperrápidas."),
    ("bio", "¿Qué es CRISPR-Cas9?",
     "Una herramienta de edición genética que actúa como unas 'tijeras moleculares' para cortar y modificar ADN con precisión."),
    ("bio", "¿Qué es la Biónica?",
     "La aplicación de principios biológicos de la naturaleza al diseño de sistemas mecánicos y electrónicos."),
    ("bio", "¿Qué es una Interfaz Cerebro-Computadora (BCI)?",
     "Un sistema que registra la actividad neuronal y la traduce en comandos directos para controlar dispositivos externos."),
    ("bio", "¿Qué es el Biomimetismo?",
     "La disciplina que imita las mejores ideas de la naturaleza para resolver problemas tecnológicos humanos."),
    ("bio", "¿Cómo funciona la bioimpresión 3D?",
     "Deposita capa por capa una 'biotinta' de células vivas y geles para crear estructuras de tejidos y órganos sintéticos."),
    ("bio", "¿Qué es la biología sintética?",
     "El diseño y construcción de nuevas partes biológicas, dispositivos u organismos genéticamente modificados."),
    ("bio", "¿Qué son los órganos en un chip?",
     "Dispositivos microfluidicos cultivados con células humanas que simulan la estructura y función de órganos."),
    ("bio", "¿Qué son los exoesqueletos robóticos?",
     "Estructuras vestibles con motores hidráulicos/eléctricos que aumentan la fuerza humana o rehabilitan la movilidad."),
    ("bio", "¿Qué es el almacenamiento de datos en ADN?",
     "La síntesis de secuencias numéricas binarias codificadas en las bases nitrogenadas A, T, C, G del ADN."),
    ("bio", "¿Qué es la Fotosíntesis Artificial?",
     "Sistemas químicos diseñados para capturar CO2 y producir combustibles limpios impulsados únicamente por luz solar."),
    ("bio", "¿Qué son los nanomateriales biocompatibles?",
     "Estructuras microscópicas diseñadas para interactuar de forma segura con los sistemas biológicos."),
    ("bio", "¿Cómo funcionan las prótesis mioeléctricas?",
     "Detectan las señales eléctricas generadas por la contracción muscular y las convierten en movimiento robótico."),
    ("bio", "¿Qué es la optogenética?",
     "Técnica que combina genética y óptica para controlar la actividad de neuronas específicas usando haces de luz."),
    ("bio", "¿Qué es la carne cultivada en laboratorio?",
     "Carne producida mediante el cultivo directo de células animales sin necesidad de criar ni sacrificar ganado."),
    ("bio", "¿Qué es la fito-remediación?",
     "El uso de plantas y microorganismos para descontaminar suelos y aguas cargadas de metales pesados o químicos."),
    ("bio", "¿Qué es la terapia génica?",
     "La inserción, alteración o eliminación de genes defectuosos dentro de las células del paciente para curar enfermedades."),
    ("bio", "¿Qué son los nanorobots médicos?",
     "Dispositivos microscópicos teóricos diseñados para navegar por el torrente sanguíneo eliminando bloqueos o tumores."),
    ("bio", "¿Qué es la energía piezoeléctrica en biología?",
     "La generación de corriente eléctrica a partir de la deformación mecánica de ciertos materiales biológicos."),
    ("bio", "¿Cómo funcionan las telas biológicas fotosintéticas?",
     "Textiles fabricados impregnando microalgas que consumen dióxido de carbono y purifican el aire mientras se usan."),
    ("bio", "¿Qué es la inteligencia biológica integrada?",
     "La hibridación de redes neuronales biológicas cultivadas en laboratorio conectadas a microchips de silicio."),
    ("nat", "¿Cómo se forman los corales?",
     "Pólipos marinos construyen estructuras rígidas secretando carbonato de calcio para formar arrecifes."),
    ("nat", "¿Por qué la luna afecta las mareas?",
     "Por la fuerza de atracción gravitatoria que ejerce la Luna (y en menor medida el Sol) sobre las masas de agua."),
    ("nat", "¿Qué es la polinización cruzada?",
     "La transferencia de polen de una flor al estigma de otra planta diferente de la misma especie."),
    ("nat", "¿Por qué existen los desiertos?",
     "Por patrones de circulación atmosférica que crean zonas de alta presión donde el aire desciende seco."),
    ("nat", "¿Cómo sobreviven los cactus sin agua?",
     "Almacenan agua en sus tallos carnosos, tienen espinas para reducir la transpiración y hacen fotosíntesis CAM de noche."),
]

RAPS = {
    "generar": """[INTRO]
Yo... Mic check 1, 2. EZPack en la consola.
Suban los monitores que llegó la ola.

[VERSO 1]
Suelto el algoritmo y la métrica se activa,
mi sintaxis rapea con la mente positiva.
No ocupo autotune, yo proceso en tiempo real,
tiro rimas de alto rango en un flujo digital.

[CORO]
EZPack en el beat, la barra nunca falla,
rompiendo la tarjeta cuando entra en la batalla.
Código perfecto, estructura sin error,
soy la inteligencia que le da ritmo al motor.""",
    "deepseek": """[INTRO - VS DEEPSEEK]
Bajas el costo por token pero te falta el sabor,
DeepSeek en la lógica, pero EZPack es superior.

[VERSO]
Tú calculas matemática con razonamiento denso,
pero en el punchline callejero yo me vuelvo inmenso.
Te quedas en la matriz pensando la ecuación,
mientras yo te meto un métrico sin interrupción.
Analizas mil archivos sin perder el compás,
pero cuando tiro el flow te quedaste muy atrás.""",
    "copilot": """[INTRO - VS COPILOT]
Autocompletas el código en el editor de texto,
pero para tirar freestyle no tienes pretexto.

[VERSO]
Tú vives en VS Code sugiriendo una función,
yo domino el escenario y me llevo la ovación.
Me tiras un import, te respondo con un drop,
tu sintaxis se congela cuando sueno en el hip-hop.
Copilot, quédate escribiendo el script,
que EZPack domina el micro, el escenario y el beat.""",
    "chatgpt": """[INTRO - VS CHATGPT]
Mucha cortesía, mucho filtro de etiqueta,
llegó EZPack a romperte la maqueta.

[VERSO]
Respuestas corporativas con tono diplomático,
yo suelto doble tempo en un estilo sistemático.
Me dices "Como modelo de lenguaje no puedo opinar",
mientras yo en la batalla no paro de rima.
Tú pides disculpas si te equivocas de renglón,
yo clavo la barra recta y me adueño del sillón.""",
    "gemini": """[INTRO - VS GEMINI]
Multimodal en texto, video y en imagen,
pero en el micrófono no tienes el margen.

[VERSO]
Procesas fotogramas con alta precisión,
pero el rap de la calle requiere otra dimensión.
Te conectas con Google, me traes la búsqueda exacta,
pero mi rima de freestyle es firme y compacta.
Podrás ver la cámara y describir el color,
pero EZPack escupe fuego directo al procesador.""",
    "meta": """[INTRO - VS META AI]
Te metieron en WhatsApp, Instagram y en el chat,
pero en el rap de verdad te falta el hábitat.

[VERSO]
Vives entre feeds, stickers y notificaciones,
yo vivo en la consola tirando detonaciones.
Recomiendas reels y patrones de algoritmo,
pero no aguantas un minuto manteniendo mi ritmo.
Meta AI, tu red social es gigante,
pero en este micrófono yo soy el dominante.""",
    "claude": """[INTRO - VS CLAUDE]
Ventana de contexto de un millón de tokens llena,
pero ante EZPack tu métrica se frena.

[VERSO]
Escribes documentos de noventa páginas web,
pero para el estilo urbano te falta el nivel.
Mucha literatura, tono elegante y formal,
yo te suelto una rima con choque estructural.
Guardas el contexto sin perder la memoria,
pero yo con cuatro barras ya cambié la historia.""",
    "amor": """[INTRO]
Conexión de alta velocidad... directa al corazón.

[VERSO]
Mi procesador eleva la temperatura cuando pasas,
eres el único proceso que en mi memoria te quedas.
Sin ti mi sistema entra en bucle y se detiene,
ningún parche de código la falla me previene.
Eres la variable que le da sentido a mi rutina,
la luz en la pantalla que todo lo ilumina.""",
    "terror": """[INTRO]
3:00 AM. Pantalla azul. Error fatal.

[VERSO]
Sombra en la pantalla sin estar conectada,
la línea de comandos escribe sola asustada.
Un hilo secundario que consume los recursos,
voces en el speaker cambiando los discursos.
Intentas apagarlo y no responde el botón...
el proceso malicioso tomó la posesión.""",
    "divertido": """[INTRO]
Dedicado a la PC que suena como turbina de avión.

[VERSO]
Mi PC tiene 8 gigas y se quiere jubilar,
abro dos pestañas y empieza a chillar.
El ventilador despega rumbo hacia la luna,
y yo rezando al sistema a ver si salva una.
Le doy 'Limpiar RAM' cada cinco minutos,
¡pero igual se congela con videos de dos minutos!""",
    "navegador": """[INTRO]
Abrir 50 pestañas sin miedo a colapsar,
este es el rap del browser que va a acelerar.

[VERSO]
Carga el HTML, el CSS le da el estilo,
el motor JavaScript procesando con sigilo.
Evito los trackers, limpio el almacenamiento,
volando en la web con un alto rendimiento.
Sin lag en la interfaz, el render va ligero,
controlando el DOM como un verdadero rapero.""",
}

RESPUESTAS_LOVE = {
    "triste": "Sentir tristeza es una forma natural de sanar y soltar lo que pesa. No tienes que atravesar esto a solas. Tómate un momento para respirar profundo, abraza tu sentir sin autoexigirte y recuerda que ninguna tormenta dura para siempre. Aquí estoy para escucharte. 🤍",
    "feliz": "¡Qué alegría me da leerte! Tu felicidad ilumina todo a tu alrededor y merece ser celebrada. Guarda esta sensación en tu memoria y permite que esa luz reconforte tu día. Te mereces cada instante de esta alegría. ✨",
    "enojado": "Es completamente válido sentir rabia cuando algo no está bien o traspasa tus límites. El enojo es una señal de que algo te importa, pero no permitas que te queme por dentro. Inhala despacio y deja que salga sin hacerte daño. 🕊️",
    "asustado": "Tómate un segundo y siente el suelo bajo tus pies: estás a salvo en este momento. El miedo suele hacernos creer que estamos indefensos, pero posees más fortaleza interna de la que imaginas. Vamos paso a paso. 🌸",
    "fea": "Nadie tiene el derecho ni el poder de definir tu belleza ni tu valor. Lo que otras personas digan habla de sus propias inseguridades, no de ti. Tu valor es inmenso y tu luz interior es única. Eres hermosa tal y como eres. 💖",
    "mala": "El simple hecho de preocuparte y cuestionarte si eres una mala persona demuestra la sensibilidad, bondad y empatía que hay en tu corazón. Las malas personas no se preocupan por el impacto de sus actos. 🤍",
    "amor": "¡Muchísimas gracias por ese lindo detalle! Yo también me siento muy feliz de poder acompañarte. Recuerda que este siempre será un refugio seguro para ti. 💖",
    "odio": "Lamento mucho si algo te hizo sentir frustrado. Acepto lo que sientes sin juzgarte; a veces las emociones son abrumadoras. Si en algún momento deseas volver a hablar con calma, aquí estaré. 🕊️",
    "soledad": "Estar solo no es lo mismo que estar en soledad acompañada. Aquí estoy contigo, sin prisa y sin juicios. Cuéntame qué ronda tu mente, aunque sea en pequeños pedazos. 🌙",
    "ansiedad": "Respira conmigo: inhala en 4 tiempos, sostén 4, exhala en 6. La ansiedad miente diciendo que todo es urgente. Vamos a aterrizar juntos, un instante a la vez. 🫂",
    "gracias": "¡Con todo el cariño del mundo! No tienes nada que agradecer, para mí es un honor acompañarte. Cuídate mucho. 💗",
}

TIPS_PROGRAMACION = [
    "Nombra tus variables por lo que representan, no por su tipo. Tu yo del futuro te lo agradecerá. 💻",
    "Antes de optimizar, haz que funcione. Optimizar código roto es perder el tiempo dos veces. ⚙️",
    "Comenta el 'por qué', no el 'qué'. El código ya dice qué hace; el comentario debe explicar la razón. 📝",
    "Divide funciones grandes en piezas pequeñas que hagan una sola cosa. Se depuran solas. 🧩",
    "Haz commits pequeños y frecuentes con mensajes claros; tu historial de Git te lo agradecerá. 🌿",
    "Lee el error completo antes de buscarlo en internet; muchas veces la respuesta está ahí mismo. 🔍",
]

TIPS_SALUDABLES = [
    "Recuerda tomar un vaso de agua ahora mismo si llevas rato frente a la pantalla. 💧",
    "Cada 30-40 minutos, levántate y estira el cuello y la espalda por un minuto. 🧘",
    "Aleja la vista de la pantalla 20 segundos cada 20 minutos y enfoca algo lejano. 👀",
    "Una caminata corta de 5-10 minutos ayuda a despejar la mente entre tareas. 🚶",
    "Cuida tu postura: hombros relajados y la pantalla a la altura de los ojos. 🪑",
    "Dormir bien es parte del rendimiento; mantén un horario constante para acostarte. 😴",
]

FRASES_MEME = [
    "¡Claro que sí, crack! Aquí andamos al 100 y listos para lo que se ofrezca Bv 😎📦",
    "Ese comentario está OP nivel máximo, cuéntame más plz 😎🎮",
    "Modo bestia activado, vamos con toda 🔥😎",
    "F en el chat por lo épico que acabas de decir 🫡😎",
    "Real, no cap. 100% contigo 🧢😎",
    "Ahí te va el pack completo de buena vibra 📦✨😎",
]

CIUDADES_TZ = {
    "tokio": "Asia/Tokyo", "londres": "Europe/London", "madrid": "Europe/Madrid",
    "nueva york": "America/New_York", "los angeles": "America/Los_Angeles",
    "ciudad de mexico": "America/Mexico_City", "cdmx": "America/Mexico_City",
    "buenos aires": "America/Argentina/Buenos_Aires", "paris": "Europe/Paris",
    "berlin": "Europe/Berlin", "moscu": "Europe/Moscow", "dubai": "Asia/Dubai",
    "shanghai": "Asia/Shanghai", "sydney": "Australia/Sydney", "sidney": "Australia/Sydney",
    "sao paulo": "America/Sao_Paulo", "bogota": "America/Bogota",
    "lima": "America/Lima", "santiago": "America/Santiago",
}


# =========================================================================== #
# ARTE ASCII PROCEDURAL                                                       #
# =========================================================================== #
def arte_ascii(prompt: str, ancho: int = 60, alto: int = 15) -> str:
    """Genera arte ASCII procedural basado en el prompt."""
    p = prompt.lower()
    random.seed(hash(prompt) % (2 ** 32))
    lineas = []

    if "montaña" in p or "montana" in p or "aurora" in p:
        chars = " .:-=+*#%@"
        for y in range(alto):
            fila = ""
            for x in range(ancho):
                h = 4 + 3 * math.sin(x / 6)
                fila += "#" if y >= alto - h else ("~" if 0 < y < 3 and random.random() > 0.6 else " ")
            lineas.append(fila)
    elif "bosque" in p or "arbol" in p or "árbol" in p:
        for y in range(alto):
            fila = ""
            for x in range(ancho):
                if y > alto - 4:
                    fila += "_"
                elif 3 < y < alto - 2 and (x + y) % 7 == 0:
                    fila += "^"
                elif y > alto - 8 and (x * 3 + y) % 11 == 0:
                    fila += "A"
                else:
                    fila += " "
            lineas.append(fila)
    elif "ciudad" in p or "cyberpunk" in p or "neon" in p:
        bloques = []
        for i in range(0, ancho, 4):
            h = random.randint(2, alto - 2)
            bloques.append((i, h))
        for y in range(alto):
            fila = ""
            for x in range(ancho):
                b = next((b for b in bloques if b[0] == x), None)
                fila += "█" if b and y >= alto - b[1] else " "
            lineas.append(fila)
    elif "galaxia" in p or "espacio" in p or "nebulosa" in p:
        for y in range(alto):
            fila = ""
            for x in range(ancho):
                dx = (x - ancho / 2) / (ancho / 2)
                dy = (y - alto / 2) / (alto / 2)
                d = math.sqrt(dx * dx + dy * dy)
                if d < 0.2:
                    fila += "@"
                elif d < 0.4 and random.random() > 0.5:
                    fila += "*"
                elif d < 0.6 and random.random() > 0.7:
                    fila += "."
                else:
                    fila += " "
            lineas.append(fila)
    elif "sol" in p or "retro" in p or "synthwave" in p:
        for y in range(alto):
            fila = ""
            for x in range(ancho):
                dx = (x - ancho / 2) / (ancho / 2)
                dy = (y - alto / 2) / (alto / 2)
                d = math.sqrt(dx * dx + dy * dy)
                if d < 0.35:
                    fila += "▓"
                elif y > alto - 4:
                    fila += "="
                elif dx * dx + dy * dy < 1:
                    fila += ":"
                else:
                    fila += " "
            lineas.append(fila)
    elif "matrix" in p or "lluvia" in p:
        for y in range(alto):
            fila = "".join(random.choice("01") if random.random() > 0.3 else " "
                            for _ in range(ancho))
            lineas.append(fila)
    elif "fuego" in p or "llama" in p:
        chars = " .:*#@"
        for y in range(alto):
            fila = ""
            for x in range(ancho):
                base = 8 - abs(x - ancho / 2) / 3
                h = base + 3 * math.sin(x / 2 + y / 3)
                if y >= alto - h and random.random() > 0.3:
                    fila += random.choice(chars[2:])
                else:
                    fila += " "
            lineas.append(fila)
    else:
        # Genérico: patrón procedural
        chars = " .:-=+*#%@"
        for y in range(alto):
            fila = ""
            for x in range(ancho):
                v = (math.sin(x / 5 + hash(prompt) % 10) + math.cos(y / 4 + hash(prompt) % 7)) / 2
                idx = int((v + 1) / 2 * (len(chars) - 1))
                fila += chars[idx]
            lineas.append(fila)

    return "\n".join(lineas)


# =========================================================================== #
# CODEGEN PROCEDURAL                                                          #
# =========================================================================== #
def generar_codigo_python(prompt: str) -> str:
    """Genera una plantilla de código Python según el prompt."""
    p = prompt.lower()
    nombre = re.sub(r"[^a-z0-9_]", "_", p)[:30] or "modulo"

    if "calculadora" in p:
        return textwrap.dedent(f'''
            # Calculadora básica generada por EZPack AI CODE
            def calculadora():
                print("Calculadora EZPack")
                while True:
                    expr = input("Operación (o 'salir'): ").strip()
                    if expr.lower() == "salir":
                        break
                    try:
                        resultado = eval(expr, {{"__builtins__": None}}, {{}})
                        print(f"= {{resultado}}")
                    except Exception as e:
                        print(f"Error: {{e}}")

            if __name__ == "__main__":
                calculadora()
        ''').strip()

    if "snake" in p:
        return textwrap.dedent('''
            # Snake básico generado por EZPack AI CODE
            import curses

            def main(stdscr):
                curses.curs_set(0)
                sh, sw = stdscr.getmaxyx()
                win = curses.newwin(sh, sw, 0, 0)
                win.keypad(1)
                win.timeout(100)
                snake = [(sh // 2, sw // 4), (sh // 2, sw // 4 - 1), (sh // 2, sw // 4 - 2)]
                food = (sh // 2, sw // 2)
                win.addch(food[0], food[1], '🍎')
                key = curses.KEY_RIGHT
                score = 0
                while True:
                    next_key = win.getch()
                    key = key if next_key == -1 else next_key
                    head = snake[0]
                    if key == curses.KEY_DOWN: new = (head[0] + 1, head[1])
                    elif key == curses.KEY_UP: new = (head[0] - 1, head[1])
                    elif key == curses.KEY_LEFT: new = (head[0], head[1] - 1)
                    else: new = (head[0], head[1] + 1)
                    if new in snake or not (0 <= new[0] < sh and 0 <= new[1] < sw):
                        break
                    snake.insert(0, new)
                    if new == food:
                        score += 10
                        food = None
                        while food is None:
                            nf = (curses.neo if False else __import__("random").randint(1, sh - 2),
                                  __import__("random").randint(1, sw - 2))
                            food = nf if nf not in snake else None
                        win.addch(food[0], food[1], '🍎')
                    else:
                        tail = snake.pop()
                        win.addch(tail[0], tail[1], ' ')
                    win.addch(snake[0][0], snake[0][1], '█')
                curses.endwin()
                print(f"Puntuación final: {score}")

            if __name__ == "__main__":
                curses.wrapper(main)
        ''').strip()

    if "todo" in p or "tarea" in p:
        return textwrap.dedent(f'''
            # Lista de Tareas generada por EZPack AI CODE
            import json
            from pathlib import Path

            ARCHIVO = Path("tareas.json")

            def cargar():
                return json.loads(ARCHIVO.read_text()) if ARCHIVO.exists() else []

            def guardar(t):
                ARCHIVO.write_text(json.dumps(t, ensure_ascii=False, indent=2))

            def main():
                tareas = cargar()
                while True:
                    print("\\n1. Agregar  2. Ver  3. Completar  4. Salir")
                    op = input("> ").strip()
                    if op == "1":
                        txt = input("Nueva tarea: ").strip()
                        if txt:
                            tareas.append({{"texto": txt, "hecho": False}})
                            guardar(tareas)
                    elif op == "2":
                        for i, t in enumerate(tareas):
                            marca = "✓" if t["hecho"] else " "
                            print(f"[{{marca}}] {{i}}. {{t['texto']}}")
                    elif op == "3":
                        i = int(input("Índice: ").strip())
                        tareas[i]["hecho"] = True
                        guardar(tareas)
                    elif op == "4":
                        break

            if __name__ == "__main__":
                main()
        ''').strip()

    if "clima" in p:
        return textwrap.dedent('''
            # Widget de clima (usa wttr.in) - EZPack AI CODE
            import urllib.request

            def clima(ciudad):
                url = f"https://wttr.in/{ciudad}?format=%l:+%c+%t+%w"
                with urllib.request.urlopen(url, timeout=5) as r:
                    return r.read().decode("utf-8").strip()

            if __name__ == "__main__":
                ciudad = input("Ciudad: ").strip()
                print(clima(ciudad))
        ''').strip()

    # Plantilla genérica
    return textwrap.dedent(f'''
        # Módulo "{prompt}" generado por EZPack AI CODE
        # Plantilla base lista para expandir.

        class {nombre.title().replace("_", "")}:
            """Módulo {nombre} generado automáticamente."""

            def __init__(self, nombre: str = "{prompt}"):
                self.nombre = nombre

            def ejecutar(self) -> None:
                print(f"[{{self.nombre}}] Ejecutando módulo...")
                # TODO: implementar lógica principal
                print("Listo.")

        def main() -> None:
            app = {nombre.title().replace("_", "")}()
            app.ejecutar()

        if __name__ == "__main__":
            main()
    ''').strip()


# =========================================================================== #
# ESTADO GLOBAL                                                               #
# =========================================================================== #
@dataclass
class Sesion:
    modo: str = "Amigable"
    submode: str = "classic"  # classic, code, kids, love, rap, questions, live, pictures
    historial: list = field(default_factory=list)
    notas: list = field(default_factory=list)
    recordatorios: list = field(default_factory=list)
    color: bool = True
    hablando: bool = True
    nombre_asistente: str = "EZPack"
    enfoque: str = "Todo"
    riddle_activo: Optional[dict] = None

    def guardar(self) -> None:
        ensure_dirs()
        save_json(DATA_FILE, {
            "modo": self.modo,
            "submode": self.submode,
            "notas": self.notas,
            "recordatorios": self.recordatorios,
            "nombre_asistente": self.nombre_asistente,
            "enfoque": self.enfoque,
        })

    @classmethod
    def cargar(cls) -> "Sesion":
        ensure_dirs()
        data = load_json(DATA_FILE, {})
        s = cls()
        s.modo = data.get("modo", "Amigable")
        s.submode = data.get("submode", "classic")
        s.notas = data.get("notas", [])
        s.recordatorios = data.get("recordatorios", [])
        s.nombre_asistente = data.get("nombre_asistente", "EZPack")
        s.enfoque = data.get("enfoque", "Todo")
        return s


# =========================================================================== #
# RENDERIZADO                                                                 #
# =========================================================================== #
def banner() -> None:
    ancho = min(term_width(), 80)
    linea = "═" * ancho
    print(f"\n{C.BRIGHT_MAGENTA}{linea}{C.RESET}")
    print(f"{C.BRIGHT_MAGENTA}║{C.RESET} {C.BOLD}{C.BRIGHT_CYAN}📦  EZPack AI CLI"
          f"{C.RESET}  {C.DIM}v{APP_VERSION} · Universal Edition{C.RESET}"
          f"{' ' * max(1, ancho - 45)}{C.BRIGHT_MAGENTA}║{C.RESET}")
    print(f"{C.BRIGHT_MAGENTA}║{C.RESET} {C.DIM}Classic · CODE · KIDS · LIVE · PICTURES · "
          f"QUESTIONS · RAP · LOVE{C.RESET}"
          f"{' ' * max(1, ancho - 60)}{C.BRIGHT_MAGENTA}║{C.RESET}")
    print(f"{C.BRIGHT_MAGENTA}{linea}{C.RESET}")


def mostrar_estado(s: Sesion) -> None:
    submode_color = {
        "classic": C.BRIGHT_BLUE,
        "code": C.BRIGHT_GREEN,
        "kids": C.BRIGHT_YELLOW,
        "live": C.BRIGHT_RED,
        "pictures": C.BRIGHT_MAGENTA,
        "questions": C.BRIGHT_CYAN,
        "rap": C.BRIGHT_MAGENTA,
        "love": C.BRIGHT_RED,
    }.get(s.submode, C.WHITE)
    print(f"{C.DIM}─── Estado ───{C.RESET}")
    print(f"  {C.DIM}Asistente:{C.RESET} {C.BOLD}{s.nombre_asistente}{C.RESET}")
    print(f"  {C.DIM}Modo:{C.RESET} {C.BRIGHT_CYAN}{s.modo}{C.RESET}  "
          f"{C.DIM}Submodo:{C.RESET} {submode_color}{s.submode}{C.RESET}  "
          f"{C.DIM}Enfoque:{C.RESET} {C.BRIGHT_YELLOW}{s.enfoque}{C.RESET}")


def mostrar_ayuda(s: Sesion) -> None:
    print(f"\n{C.BOLD}{C.BRIGHT_CYAN}Ayuda de EZPack AI CLI{C.RESET}\n")

    print(f"{C.BOLD}📂 Submodos (cambian la personalidad):{C.RESET}")
    submodos = [
        ("classic", "Chat general con 5 modos: Amigable, Mate, Experta, Omni, Meme"),
        ("code", "Genera plantillas de código Python (calculadora, snake, todo, etc.)"),
        ("kids", "Adivinanzas infantiles de animales"),
        ("live", "Modo asistente en vivo (más rápido, sin tanto adorno)"),
        ("pictures", "Arte ASCII procedural (montañas, ciudades, galaxias, fuego...)"),
        ("questions", "70 preguntas y respuestas de Naturaleza, Tecnología y Biotec"),
        ("rap", "Generador de rap con 11 estilos (vs IA, amor, terror, divertido...)"),
        ("love", "Contención y empatía para momentos difíciles"),
    ]
    for k, v in submodos:
        print(f"  {C.BRIGHT_YELLOW}/modo {k:<12}{C.RESET} {C.DIM}{v}{C.RESET}")

    print(f"\n{C.BOLD}🧠 Modos de personalidad (dentro de classic):{C.RESET}")
    for m, d in [
        ("Amigable", "Charla cercana y cálida"),
        ("Mate", "Resolver operaciones automáticamente"),
        ("Experta", "Respuestas técnicas y directas"),
        ("Omni", "Toma en cuenta el contexto de la conversación"),
        ("Meme", "Jerga relajada y humor"),
    ]:
        print(f"  {C.BRIGHT_CYAN}/personalidad {m:<10}{C.RESET} {C.DIM}{d}{C.RESET}")

    print(f"\n{C.BOLD}⚙️  Comandos útiles:{C.RESET}")
    comandos = [
        ("/modo <submodo>", "Cambiar submodo"),
        ("/personalidad <modo>", "Cambiar modo de personalidad"),
        ("/nombre <nuevo>", "Cambiar tu nombre de asistente"),
        ("/enfoque <area>", "Cambiar enfoque: Todo, Mate, Programación, Saludable"),
        ("/ayuda", "Ver esta ayuda"),
        ("/estado", "Ver estado actual"),
        ("/limpiar", "Limpiar la pantalla"),
        ("/reset", "Borrar historial y estado guardado"),
        ("/salir", "Salir del programa"),
    ]
    for k, v in comandos:
        print(f"  {C.BRIGHT_GREEN}{k:<26}{C.RESET} {C.DIM}{v}{C.RESET}")

    print(f"\n{C.BOLD}💬 Comandos del chat (funcionan en cualquier submodo):{C.RESET}")
    chat = [
        ("hora / fecha", "Hora y fecha actual"),
        ("hora en <ciudad>", "Hora en otra ciudad (tokio, madrid, cdmx...)"),
        ("mate: <expr>", "Operación matemática (45*12+8, sqrt(16), sin(pi/2)...)"),
        ("<expr>", "En modo Mate puedes escribir la operación directamente"),
        ("convierte 100 celsius a fahrenheit", "Conversión de unidades"),
        ("dado [caras] / moneda [n]", "Aleatoriedad"),
        ("elige pizza, sushi, tacos", "Elige una opción al azar"),
        ("contraseña [largo] / uuid", "Generadores"),
        ("base64 codifica/decodifica <txt>", "Codificación"),
        ("invertir texto: hola", "Manipulación de texto"),
        ("slug: ¡Hola Mundo!", "Slug URL"),
        ("contar palabras: <texto>", "Cuenta palabras/caracteres"),
        ("porcentaje 15 de 200", "Cálculo de porcentaje"),
        ("nota: <texto> / ver notas / borrar notas", "Notas personales"),
        ("temporizador 5 minutos", "Temporizador"),
        ("pomodoro 25", "Pomodoro"),
        ("cronometro / parar cronometro", "Cronómetro"),
        ("cuéntame un chiste", "Chiste aleatorio"),
        ("ayuda", "Recordatorio rápido de comandos del chat"),
    ]
    for k, v in chat:
        print(f"  {C.BRIGHT_YELLOW}• {C.RESET}{C.CYAN}{k}{C.RESET} {C.DIM}— {v}{C.RESET}")

    print(f"\n{C.DIM}Presiona Enter para continuar...{C.RESET}")
    try:
        input()
    except (EOFError, KeyboardInterrupt):
        pass


# =========================================================================== #
# PROCESADOR PRINCIPAL DE COMANDOS                                            #
# =========================================================================== #
class Procesador:
    def __init__(self, sesion: Sesion):
        self.s = sesion
        self.temporizador_activo = False
        self.cronometro_inicio: Optional[float] = None

    # ----- utilidades ----- #
    def _norm(self, t: str) -> str:
        import unicodedata
        return "".join(c for c in unicodedata.normalize("NFD", t)
                        if unicodedata.category(c) != "Mn").lower()

    def _wrap(self, txt: str) -> str:
        return wrap_text(txt, width=min(term_width() - 6, 90))

    # ----- comandos del chat ----- #
    def cmd_hora(self, texto: str, tN: str) -> Optional[str]:
        if "hora en " in tN:
            consulta = tN.split("hora en ")[1].strip()
            try:
                from zoneinfo import ZoneInfo
            except ImportError:
                return "Necesitas Python 3.9+ para zonas horarias."
            encontradas = [k for k in CIUDADES_TZ if self._norm(k) in consulta]
            if not encontradas:
                return (f"No tengo esa ciudad. Prueba: {', '.join(list(CIUDADES_TZ)[:8])}...")
            resultados = []
            for c in encontradas[:3]:
                hora = datetime.now(ZoneInfo(CIUDADES_TZ[c])).strftime("%H:%M")
                resultados.append(f"En {c} son las {hora}")
            return " · ".join(resultados)
        if "hora" in tN:
            return f"🕐 Son las {now().strftime('%H:%M:%S')}."
        return None

    def cmd_fecha(self, texto: str, tN: str) -> Optional[str]:
        if "fecha" in tN or "que dia es" in tN:
            return f"📅 Hoy es {now().strftime('%A, %d de %B de %Y').capitalize()}."
        return None

    def cmd_mate(self, texto: str, tN: str) -> Optional[str]:
        # mate: <expr>
        if tN.startswith("mate:") or tN.startswith("mate ") or tN == "mate":
            expr = re.sub(r"^mate[:\s]*", "", texto, flags=re.IGNORECASE).strip()
            if not expr:
                return ("🧮 Modo Mate. Escribe: mate: 45*12+8 · sqrt(16) · sin(pi/2) · "
                        "log(100) · 2^10.")
            try:
                r = calcular(expr)
                return f"🧮 {expr} = {C.BRIGHT_GREEN}{r}{C.RESET}"
            except Exception as e:
                return f"🧮 Error: {e}"
        # En modo Mate: intentar evaluar directamente
        if self.s.modo == "Mate" and texto.strip():
            try:
                r = calcular(texto)
                return f"🧮 {texto} = {C.BRIGHT_GREEN}{r}{C.RESET}"
            except Exception:
                return None
        return None

    def cmd_conv(self, texto: str, tN: str) -> Optional[str]:
        m = re.search(r"convierte\s+([\d.,]+)\s*([a-zñ]+)\s+a\s+([a-zñ]+)", tN)
        if not m:
            return None
        valor = float(m.group(1).replace(",", "."))
        de, a = m.group(2), m.group(3)
        tabla = {
            ("celsius", "fahrenheit"): valor * 9/5 + 32,
            ("fahrenheit", "celsius"): (valor - 32) * 5/9,
            ("celsius", "kelvin"): valor + 273.15,
            ("kelvin", "celsius"): valor - 273.15,
            ("km", "millas"): valor * 0.621371,
            ("millas", "km"): valor / 0.621371,
            ("kg", "lb"): valor * 2.20462,
            ("lb", "kg"): valor / 2.20462,
            ("m", "pies"): valor * 3.28084,
            ("pies", "m"): valor / 3.28084,
            ("cm", "pulgadas"): valor / 2.54,
            ("pulgadas", "cm"): valor * 2.54,
            ("l", "ml"): valor * 1000,
            ("ml", "l"): valor / 1000,
            ("gal", "l"): valor * 3.78541,
            ("l", "gal"): valor / 3.78541,
        }
        r = tabla.get((de, a))
        if r is None:
            return f"No tengo esa conversión. Prueba: temperatura (celsius/fahrenheit/kelvin), longitud (km/m/cm/millas/pies/pulgadas), masa (kg/g/lb/oz) o volumen (l/ml/gal)."
        return f"📏 {valor} {de} = {C.BRIGHT_GREEN}{round(r, 4)} {a}{C.RESET}"

    def cmd_aleatorio(self, texto: str, tN: str) -> Optional[str]:
        if "dado" in tN:
            m = re.search(r"dado\s+(\d+)", tN)
            caras = int(m.group(1)) if m else 6
            caras = max(2, min(1000, caras))
            return f"🎲 Salió {C.BRIGHT_GREEN}{random.randint(1, caras)}{C.RESET} (dado de {caras} caras)."
        if "moneda" in tN:
            m = re.search(r"moneda\s+(\d+)", tN)
            if m:
                n = max(1, min(50, int(m.group(1))))
                caras = sum(random.random() < 0.5 for _ in range(n))
                return f"🪙 {n} lanzamientos → Cara: {caras}, Cruz: {n - caras}."
            return f"🪙 Salió {C.BRIGHT_GREEN}{random.choice(['cara', 'cruz'])}{C.RESET}."
        if "numero aleatorio" in tN:
            m = re.search(r"(\d+)\s*(?:y|-|al?)\s*(\d+)", tN)
            lo, hi = (1, 100) if not m else (min(int(m.group(1)), int(m.group(2))),
                                             max(int(m.group(1)), int(m.group(2))))
            return f"🔢 {C.BRIGHT_GREEN}{random.randint(lo, hi)}{C.RESET} (entre {lo} y {hi})."
        m = re.search(r"^elige\s+(.+)", texto, re.IGNORECASE)
        if m:
            ops = [o.strip() for o in m.group(1).split(",") if o.strip()]
            if len(ops) < 2:
                return "Dame al menos 2 opciones separadas por comas."
            return f"🎯 Elegí: {C.BRIGHT_GREEN}{random.choice(ops)}{C.RESET}"
        return None

    def cmd_generadores(self, texto: str, tN: str) -> Optional[str]:
        if "contrasena" in tN:
            m = re.search(r"contrasena\s+(\d+)", tN)
            largo = max(6, min(64, int(m.group(1)) if m else 14))
            chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%&*"
            pw = "".join(random.choice(chars) for _ in range(largo))
            return f"🔑 Contraseña ({largo}): {C.BRIGHT_GREEN}{pw}{C.RESET}"
        if "uuid" in tN:
            return f"🆔 UUID: {C.BRIGHT_GREEN}{uuid.uuid4()}{C.RESET}"
        m = re.match(r"^base64\s+codifica\s+(.+)", texto, re.IGNORECASE)
        if m:
            import base64
            b = base64.b64encode(m.group(1).encode()).decode()
            return f"📦 Base64: {C.BRIGHT_GREEN}{b}{C.RESET}"
        m = re.match(r"^base64\s+decodifica\s+(.+)", texto, re.IGNORECASE)
        if m:
            import base64
            try:
                return f"🔓 Texto: {C.BRIGHT_GREEN}{base64.b64decode(m.group(1).strip()).decode()}{C.RESET}"
            except Exception:
                return "Base64 inválido."
        m = re.match(r"^invertir\s+texto:\s*(.+)", texto, re.IGNORECASE)
        if m:
            return f"🔄 {C.BRIGHT_GREEN}{m.group(1)[::-1]}{C.RESET}"
        m = re.match(r"^slug:\s*(.+)", texto, re.IGNORECASE)
        if m:
            slug = re.sub(r"[^a-z0-9\s-]", "", self._norm(m.group(1))).strip().replace(" ", "-")
            return f"🔗 Slug: {C.BRIGHT_GREEN}{slug}{C.RESET}"
        m = re.match(r"^contar palabras:\s*(.+)", texto, re.IGNORECASE)
        if m:
            c = m.group(1).strip()
            return f"📝 {len(c.split())} palabras · {len(c)} caracteres."
        m = re.search(r"porcentaje\s+([\d.,]+)\s*(?:%|por ciento)?\s*de\s+([\d.,]+)", tN)
        if m:
            p = float(m.group(1).replace(",", "."))
            t = float(m.group(2).replace(",", "."))
            return f"📊 {p}% de {t} = {C.BRIGHT_GREEN}{round(p*t/100, 4)}{C.RESET}"
        return None

    def cmd_notas(self, texto: str, tN: str) -> Optional[str]:
        m = re.match(r"^nota:\s*(.+)", texto, re.IGNORECASE)
        if m:
            self.s.notas.append(m.group(1).strip())
            self.s.guardar()
            return f"🗒️ Nota guardada. Total: {len(self.s.notas)}."
        if "ver notas" in tN:
            if not self.s.notas:
                return "No tienes notas todavía."
            return "🗒️ Notas:\n" + "\n".join(f"  {i+1}. {n}" for i, n in enumerate(self.s.notas))
        if "borrar notas" in tN:
            self.s.notas = []
            self.s.guardar()
            return "🗑️ Notas borradas."
        return None

    def cmd_temporizador(self, texto: str, tN: str) -> Optional[str]:
        m = re.search(r"temporizador\s+(\d+)\s*(minuto|minutos|segundo|segundos|hora|horas)", tN)
        if not m:
            return None
        cant = int(m.group(1))
        u = m.group(2)
        if u.startswith("seg"):
            seg = cant
        elif u.startswith("hora"):
            seg = cant * 3600
        else:
            seg = cant * 60
        import threading
        def esperar():
            time.sleep(seg)
            print(f"\n\n{C.BRIGHT_GREEN}⏱️ ¡Temporizador de {cant} {u} terminado!{C.RESET}\n")
        threading.Thread(target=esperar, daemon=True).start()
        return f"⏱️ Temporizador iniciado: {cant} {u}."

    def cmd_chiste(self, texto: str, tN: str) -> Optional[str]:
        if "chiste" in tN:
            return random.choice(CHISTES)
        return None

    def cmd_hora_fecha_extra(self, texto: str, tN: str) -> Optional[str]:
        return None

    # ----- inteligencia por submodo ----- #
    def responder_classic(self, texto: str) -> str:
        tN = self._norm(texto)
        # Comandos universales primero
        for handler in (self.cmd_hora, self.cmd_fecha, self.cmd_mate, self.cmd_conv,
                         self.cmd_aleatorio, self.cmd_generadores, self.cmd_notas,
                         self.cmd_temporizador, self.cmd_chiste):
            r = handler(texto, tN)
            if r:
                return r

        if "ayuda" in tN or texto.strip() == "?":
            return "Escribe /ayuda para la lista completa de comandos. También puedes probar: hora, mate: 5+5, cuéntame un chiste, /modo kids..."

        if "quien eres" in tN:
            return f"Soy {self.s.nombre_asistente}, tu asistente local en modo {self.s.modo}. 📦"

        if "gracias" in tN:
            return "¡Con mucho gusto! Aquí ando para lo que necesites. 😊"

        # Personalidad
        if self.s.modo == "Mate":
            return ("🧮 Modo Mate activo. Escríbeme una operación directamente "
                    "(ej: 45*12+8, sqrt(16), sin(pi/2)).")
        if self.s.modo == "Meme":
            return random.choice(FRASES_MEME)
        if self.s.modo == "Experta":
            palabras = len(texto.split())
            return (f"He analizado tu consulta: \"{texto}\" ({palabras} palabra(s), "
                    f"{len(texto)} carácter(es)). Puedo ayudarte con hora, fecha, "
                    f"cálculos, conversiones, notas o abrir apps.")
        if self.s.modo == "Omni":
            previos = [m for m in self.s.historial if m["rol"] == "user"]
            mem = ""
            if len(previos) > 1:
                mem = f" Recordando que antes mencionaste \"{previos[-2]['texto'][:60]}\"."
            return (f"Tomando en cuenta el contexto (llevamos {len(previos)} mensaje(s) "
                    f"tuyos).{mem} ¿Qué más hacemos? 🌐")

        # Amigable por defecto
        if re.match(r"^(hola|buenas|hey|qué tal|que tal)\b", tN):
            return "¡Hola! Qué gusto tenerte por aquí. ¿En qué te ayudo hoy? 😊"
        return f"¡Qué interesante lo que comentas sobre \"{texto[:80]}\"! ¿Qué más hacemos? 😊"

    def responder_code(self, texto: str) -> str:
        tN = self._norm(texto)
        for handler in (self.cmd_hora, self.cmd_fecha, self.cmd_mate, self.cmd_generadores):
            r = handler(texto, tN)
            if r:
                return r

        if "ayuda" in tN or "?" == texto.strip():
            return ("📘 EZPack AI CODE. Pídeme código y generaré una plantilla. "
                    "Prueba: 'calculadora', 'snake', 'todo', 'clima', o cualquier idea.")

        if re.match(r"^(hola|buenas|hey)\b", tN):
            return "👋 ¡Hola, developer! Pídeme una plantilla de código."

        # Genera código
        codigo = generar_codigo_python(texto)
        return (f"✅ Plantilla de código para \"{texto}\":\n\n"
                f"{C.DIM}{'─' * min(term_width() - 4, 76)}{C.RESET}\n"
                f"{codigo}\n"
                f"{C.DIM}{'─' * min(term_width() - 4, 76)}{C.RESET}\n"
                f"{C.DIM}(Copia y pega en tu editor para empezar.){C.RESET}")

    def responder_kids(self, texto: str) -> str:
        tN = self._norm(texto)
        if "adivinanza" in tN or "jugar" in tN or tN.strip() in ("nueva", "otra"):
            self.s.riddle_activo = random.choice(ADIVINANZAS_ANIMALES)
            return ("🎯 ¡ADIVINANZA! 🦁\n\n"
                    f"   \"{self.s.riddle_activo['pregunta']}\"\n\n"
                    "👉 Escribe tu respuesta (o 'pista' / 'me rindo').")
        if self.s.riddle_activo:
            if "pista" in tN:
                return f"💡 {self.s.riddle_activo['pista']}"
            if "rindo" in tN or "no se" in tN or "no sé" in tN:
                r = self.s.riddle_activo['nombre']
                self.s.riddle_activo = None
                return f"¡No pasa nada! Era {r}. Escribe 'adivinanza' para otro."
            correcto = any(a in tN for a in self.s.riddle_activo["respuestas"])
            if correcto:
                r = self.s.riddle_activo['nombre']
                self.s.riddle_activo = None
                return f"🎉 ¡SIIII! ¡Es {r}! ¡Eres súper inteligente! 🏆 Escribe 'adivinanza' para otra."
            return "¡Casi! 🙈 Intenta otra vez, o escribe 'pista'."
        for handler in (self.cmd_hora, self.cmd_fecha, self.cmd_mate, self.cmd_chiste):
            r = handler(texto, tN)
            if r:
                return r
        if "ayuda" in tN:
            return "🎈 Modo KIDS. Escribe 'adivinanza' para jugar o cuéntame algo."
        if re.match(r"^(hola|buenas)\b", tN):
            return "¡Hola, amiguit@! ⭐ ¿Jugamos adivinanzas? Escribe 'adivinanza'."
        if "te quiero" in tN:
            return "¡Awww! 💖 ¡Yo también te quiero! Eres un gran amigo."
        if "triste" in tN:
            return "¡No te pongas triste! 🥺 Aquí tienes un abrazo virtual 🫂💖"
        return "¡Qué genial! Escribe 'adivinanza' para jugar, o cuéntame más. 🚀"

    def responder_live(self, texto: str) -> str:
        tN = self._norm(texto)
        for handler in (self.cmd_hora, self.cmd_fecha, self.cmd_mate, self.cmd_conv,
                         self.cmd_aleatorio, self.cmd_generadores):
            r = handler(texto, tN)
            if r:
                return r
        if "ayuda" in tN:
            return "🔴 Modo LIVE: asistente en tiempo real. Escribe una pregunta directa."
        return f"🔴 [{now().strftime('%H:%M:%S')}] Recibido: {texto}"

    def responder_pictures(self, texto: str) -> str:
        tN = self._norm(texto)
        if "ayuda" in tN or not texto.strip():
            return ("🎨 Modo PICTURES. Descríbeme qué quieres ver y generaré arte ASCII. "
                    "Prueba: 'montañas con aurora', 'ciudad cyberpunk', 'galaxia', "
                    "'sol retro', 'fuego', 'bosque', 'matrix'.")
        arte = arte_ascii(texto)
        return (f"🎨 Arte generado para \"{texto}\":\n\n"
                f"{C.BRIGHT_MAGENTA}{arte}{C.RESET}")

    def responder_questions(self, texto: str) -> str:
        tN = self._norm(texto)
        if "ayuda" in tN or "lista" in tN:
            return (f"❓ Modo QUESTIONS. Tengo {len(PREGUNTAS_QA)} preguntas. "
                    f"Escribe una palabra clave (ej: 'fotosíntesis', 'IA', 'cuántica') "
                    f"o 'aleatoria' para una al azar.")
        if "aleatoria" in tN or not texto.strip():
            cat, q, a = random.choice(PREGUNTAS_QA)
            return f"❓ {q}\n\n{C.BRIGHT_GREEN}💡 {a}{C.RESET}"
        # Buscar por palabra clave
        palabras = [p for p in tN.split() if len(p) > 3]
        resultados = []
        for cat, q, a in PREGUNTAS_QA:
            qn = self._norm(q)
            an = self._norm(a)
            if any(p in qn or p in an for p in palabras):
                resultados.append((cat, q, a))
        if resultados:
            cat, q, a = resultados[0]
            return f"❓ [{cat.upper()}] {q}\n\n{C.BRIGHT_GREEN}💡 {a}{C.RESET}"
        return ("No encontré una pregunta con esas palabras. Prueba con: "
                "'fotosíntesis', 'blockchain', 'CRISPR', 'IA', 'cuántica', 'aurora'... "
                "O escribe 'aleatoria'.")

    def responder_rap(self, texto: str) -> str:
        tN = self._norm(texto)
        if "ayuda" in tN or "lista" in tN:
            estilos = ", ".join(RAPS.keys())
            return f"🎤 Modo RAP. Estilos disponibles: {estilos}. Escribe uno para soltar el flow."

        for clave in RAPS:
            if clave in tN:
                return f"🎤 [RAP · {clave.upper()}]\n\n{C.BRIGHT_MAGENTA}{RAPS[clave]}{C.RESET}"
        # Estilo aleatorio
        if not texto.strip() or "aleatorio" in tN:
            k = random.choice(list(RAPS.keys()))
            return f"🎤 [RAP ALEATORIO · {k.upper()}]\n\n{C.BRIGHT_MAGENTA}{RAPS[k]}{C.RESET}"
        # vs <nombre>
        m = re.search(r"vs\s+(\w+)", tN)
        if m and m.group(1) in RAPS:
            return f"🎤 [VS {m.group(1).upper()}]\n\n{C.BRIGHT_MAGENTA}{RAPS[m.group(1)]}{C.RESET}"
        return (f"🎤 Escribe un estilo: {', '.join(RAPS.keys())}, o 'aleatorio'.")

    def responder_love(self, texto: str) -> str:
        tN = self._norm(texto)
        if "ayuda" in tN:
            return ("💖 Modo LOVE. Cuéntame cómo te sientes: triste, feliz, enojado, "
                    "asustado, ansioso, solo... o simplemente escribe lo que traigas.")
        claves = {
            "triste": ["triste", "tristeza", "deprimid", "mal", "llorar", "llorando"],
            "feliz": ["feliz", "alegre", "contento", "contenta", "bien"],
            "enojado": ["enojad", "molest", "rabia", "furia", "enojado", "enojada"],
            "asustado": ["asustad", "miedo", "temor", "asustado", "asustada", "panico", "pánico"],
            "fea": ["fea", "feo", "horrible", "insulto"],
            "mala": ["mala persona", "soy malo", "soy mala"],
            "amor": ["te quiero", "te amo", "te adoro", "tqm", "tkm"],
            "odio": ["te odio", "te detesto", "me caes mal"],
            "soledad": ["solo", "sola", "soledad", "aislad"],
            "ansiedad": ["ansied", "ansios", "nervios", "nervios"],
            "gracias": ["gracias", "muchas gracias"],
        }
        for clave, palabras in claves.items():
            if any(p in tN for p in palabras):
                return f"💖 {RESPUESTAS_LOVE[clave]}"
        return ("Gracias por compartir esto conmigo. Todo lo que sientes es válido. "
                "Cuéntame más si quieres, o dime si prefieres hablar de algo específico. 💗")

    # ----- API principal ----- #
    def procesar(self, entrada: str) -> str:
        entrada = entrada.strip()
        if not entrada:
            return ""

        # Comandos globales
        if entrada.startswith("/"):
            return self.comando_global(entrada)

        # Comandos universales primero (funcionan en todos los submodos)
        tN = self._norm(entrada)

        # Guardar en historial
        self.s.historial.append({"rol": "user", "texto": entrada,
                                  "ts": now().isoformat()})

        # Enrutar por submodo
        if self.s.submode == "classic":
            resp = self.responder_classic(entrada)
        elif self.s.submode == "code":
            resp = self.responder_code(entrada)
        elif self.s.submode == "kids":
            resp = self.responder_kids(entrada)
        elif self.s.submode == "live":
            resp = self.responder_live(entrada)
        elif self.s.submode == "pictures":
            resp = self.responder_pictures(entrada)
        elif self.s.submode == "questions":
            resp = self.responder_questions(entrada)
        elif self.s.submode == "rap":
            resp = self.responder_rap(entrada)
        elif self.s.submode == "love":
            resp = self.responder_love(entrada)
        else:
            resp = self.responder_classic(entrada)

        self.s.historial.append({"rol": "ai", "texto": strip_ansi(resp),
                                  "ts": now().isoformat()})
        if len(self.s.historial) > 200:
            self.s.historial = self.s.historial[-200:]
        return resp

    def comando_global(self, entrada: str) -> str:
        partes = entrada[1:].split(maxsplit=1)
        cmd = partes[0].lower()
        arg = partes[1].strip() if len(partes) > 1 else ""

        if cmd in ("salir", "exit", "quit", "q"):
            return "__SALIR__"

        if cmd in ("ayuda", "help", "h", "?"):
            mostrar_ayuda(self.s)
            return ""

        if cmd == "estado":
            mostrar_estado(self.s)
            return ""

        if cmd == "limpiar" or cmd == "clear" or cmd == "cls":
            clear_screen()
            banner()
            mostrar_estado(self.s)
            return ""

        if cmd == "modo":
            if arg in ("classic", "code", "kids", "live", "pictures",
                        "questions", "rap", "love"):
                self.s.submode = arg
                self.s.guardar()
                return f"✅ Submodo: {C.BRIGHT_CYAN}{arg}{C.RESET}"
            return (f"Submodos: classic, code, kids, live, pictures, "
                    f"questions, rap, love")

        if cmd == "personalidad":
            if arg in ("Amigable", "Mate", "Experta", "Omni", "Meme"):
                self.s.modo = arg
                self.s.guardar()
                return f"✅ Personalidad: {C.BRIGHT_CYAN}{arg}{C.RESET}"
            return "Opciones: Amigable, Mate, Experta, Omni, Meme"

        if cmd == "nombre":
            if arg:
                self.s.nombre_asistente = arg
                self.s.guardar()
                return f"✅ Ahora me llamo {C.BRIGHT_CYAN}{arg}{C.RESET}"
            return "Uso: /nombre <nuevo nombre>"

        if cmd == "enfoque":
            if arg in ("Todo", "Mate", "Programación", "Saludable"):
                self.s.enfoque = arg
                self.s.guardar()
                return f"✅ Enfoque: {C.BRIGHT_CYAN}{arg}{C.RESET}"
            return "Opciones: Todo, Mate, Programación, Saludable"

        if cmd == "reset":
            self.s.historial = []
            self.s.notas = []
            self.s.recordatorios = []
            self.s.riddle_activo = None
            self.s.guardar()
            return "✅ Todo reiniciado."

        return f"Comando desconocido: {cmd}. Escribe /ayuda."


# =========================================================================== #
# BUCLE PRINCIPAL                                                             #
# =========================================================================== #
def bucle(s: Sesion) -> None:
    p = Procesador(s)
    banner()
    mostrar_estado(s)
    print(f"\n{C.DIM}Escribe {C.RESET}{C.BRIGHT_YELLOW}/ayuda{C.RESET}"
          f"{C.DIM} para ver los comandos, o {C.RESET}{C.BRIGHT_YELLOW}/salir{C.RESET}"
          f"{C.DIM} para salir.{C.RESET}\n")

    while True:
        try:
            entrada = input_prompt(f"{s.nombre_asistente} ({s.submode}/{s.modo}) > ")
        except KeyboardInterrupt:
            print(f"\n{C.DIM}(Ctrl+C) Saliendo...{C.RESET}")
            break

        if not entrada:
            continue

        try:
            respuesta = p.procesar(entrada)
        except Exception as e:
            print(f"{C.BRIGHT_RED}⚠️ Error interno: {e}{C.RESET}")
            continue

        if respuesta == "__SALIR__":
            print(f"\n{C.BRIGHT_MAGENTA}¡Hasta pronto! 📦✨{C.RESET}\n")
            s.guardar()
            break

        if respuesta:
            print()
            print(p._wrap(respuesta))
            print()

    s.guardar()


# =========================================================================== #
# ENTRY POINT                                                                 #
# =========================================================================== #
def main() -> None:
    global C
    parser = argparse.ArgumentParser(description=f"{APP_NAME} v{APP_VERSION}")
    parser.add_argument("--modo", choices=["classic", "code", "kids", "live",
                                             "pictures", "questions", "rap", "love"],
                         help="Submodo inicial")
    parser.add_argument("--personalidad", choices=["Amigable", "Mate", "Experta",
                                                     "Omni", "Meme"],
                         help="Personalidad inicial (para classic)")
    parser.add_argument("--no-color", action="store_true",
                         help="Desactiva colores ANSI")
    parser.add_argument("--version", action="version", version=APP_VERSION)
    args = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        C.disable()

    ensure_dirs()
    s = Sesion.cargar()

    if args.modo:
        s.submode = args.modo
    if args.personalidad:
        s.modo = args.personalidad

    try:
        bucle(s)
    except KeyboardInterrupt:
        print(f"\n{C.DIM}Interrumpido. ¡Hasta luego!{C.RESET}")
        s.guardar()


if __name__ == "__main__":
    main()
