# Plan de trabajo: LittleCat v1.1 → v1.4

**Objetivo:** que LittleCat se sienta como una mascota que **vive en tu escritorio, te acompaña mientras trabajas y juega contigo**, sin volverse molesta ni estresante.

**Fuera de alcance por ahora:** que el gato se multiplique al estilo Shimeji. Para tener otro gato ya existe la opción del menú, y los gatos de otros solo aparecen como *visitantes* (Fase 4).

Cada fase se publica como una versión con `git tag vX.Y.Z` (ver [RELEASING.md](RELEASING.md)).

---

## Reglas para todas las fases

1. **Mascota tierna, no estresante.** Todo lo nuevo tiene un ajuste en [config.py](../src/config.py) para apagarlo, y nada interrumpe al usuario cuando está concentrado.
2. **Privacidad.** No se registran teclas ni se guardan capturas de pantalla. Para saber si el usuario está activo solo se usa `GetLastInputInfo`, que dice *cuándo* hubo actividad, no *qué* se escribió.
3. **Sin transparencia alfa** en la overlay: se sigue usando el color clave magenta con sprites pixel-art.
4. **Rendimiento:** menos de 3 % de CPU con el gato en reposo y menos de 8 % con el Screen Agent activo.
5. **Cada tarea incluye un test** o una simulación sin ventana (`SDL_VIDEODRIVER=dummy`) que pueda correr en el CI.
6. **Todo lo de Windows** (ventanas, entrada) va en un solo módulo, `src/desktop.py`, hecho con `ctypes`. Si una llamada falla, el juego sigue funcionando sin esa función.

---

## Fase 1 · v1.1 "Vive en tu escritorio" (~1 semana)

**Estado:** implementada en la rama `feature/phase1-desktop`. Código en [desktop.py](../src/desktop.py) (acceso a Windows) y [desktop_life.py](../src/desktop_life.py) (comportamiento); tests en [test_desktop_life.py](../test_desktop_life.py). Cada función se apaga por separado en [config.py](../src/config.py).

| # | Tarea | Detalle | Archivos | Listo cuando… |
|---|---|---|---|---|
| 1.1 | **Módulo `desktop.py`** | Funciones para leer las ventanas visibles con su rectángulo real (`EnumWindows`, `DwmGetWindowAttribute`), la ventana activa, los monitores y el tiempo sin actividad (`GetLastInputInfo`). Se ignoran ventanas minimizadas, de sistema y la propia overlay. | `src/desktop.py` (nuevo) | El test lista ventanas sin errores y devuelve una lista vacía si no está en Windows |
| 1.2 | **Seguir el cursor** (como oneko) | Nueva acción `chase_cursor` en la autonomía: si el cursor se mueve cerca y el gato tiene energía, lo persigue; cuando el cursor se queda quieto, se sienta y luego se duerme. Tiene un tiempo de espera para no hacerlo sin parar. | `autonomy.py`, `game.py` | Persigue unos segundos, se cansa, y nunca tapa el cursor |
| 1.3 | **Sentarse sobre ventanas** | El gato puede elegir subirse a la barra de título de la ventana activa o de otra visible. Si la ventana se mueve, el gato se mueve con ella; si se cierra o se minimiza, el gato cae. | `desktop.py`, `game.py`, `autonomy.py` (acción `perch`) | Sigue a la ventana al moverla y cae al cerrarla |
| 1.4 | **Física al soltarlo** | Ya se puede arrastrar (`ALLOW_DRAG`). Falta medir la velocidad al soltarlo, aplicar gravedad y rebote en el suelo y en los bordes de la pantalla, y que aterrice en una postura propia. Si lo lanzan fuerte dice "¡wiii!", nunca se enfada. | `game.py` | Se lanza, rebota, aterriza y no sale de la pantalla en ningún monitor |
| 1.5 | **Varios monitores** | La zona donde camina y cae es la unión de todos los monitores, no solo el principal. | `desktop.py`, `game.py` | Puede cruzar de un monitor a otro caminando |
| 1.6 | **Regalos tiernos** (como Desktop Goose, en suave) | Una o dos veces al día deja junto a él un regalo pixel-art (pluma, flor o pez de papel). Al hacer clic, el regalo muestra un recuerdo sacado de `memory_graph` ("¿te acuerdas cuando jugamos con la pelota?"). | `game.py`, `cat_voice.py`, `memory_graph.py` | Como máximo 2 regalos al día, se cierran solos y nunca tapan ventanas |

---

## Fase 2 · v1.2 Screen Agent → "Mira cómo juego" (~2 semanas)

**Estado:** tareas 2.1 a 2.9 implementadas en la rama `feature/phase2-arcade`; la 2.10 (RL) queda como opcional. Pruebas en [test_screen_agent.py](../test_screen_agent.py), con 17 tests.

| Métrica (Pong propio, captura a 30 fps, 50 ms de retardo) | Resultado |
|---|---|
| Política antigua (seguir la pelota) | 92 % de aciertos |
| Predicción | 96 % de aciertos, rallies ~1.5× más largos |
| Detección sin calibrar, en el escritorio real | 98–99 % de frames, 28–29 fps, 20 de 20 pelotas |
| Imitación (copiando a un jugador imperfecto) | 94 % de aciertos (quedarse quieto: 18 %) |

Notas:
- **2.3:** la captura usa GDI con `ctypes` en lugar de `mss`, así que no añade dependencias.
- **2.7:** los puntos se miden con eventos (golpe o fallo según el movimiento de la pelota), no leyendo el marcador.
- **2.8:** el arcade vive en la overlay. El gato juega al Pong propio sentado encima de la máquina; en juegos externos se usa la línea de comandos.

Hoy [screen_agent_poc.py](../src/screen_agent_poc.py) es un script aparte: detecta por color, apunta a la x actual de la pelota, se bloquea mientras pulsa una tecla y no entra en el `.exe` porque usa `cv2`.

| # | Tarea | Detalle | Archivos | Listo cuando… |
|---|---|---|---|---|
| 2.1 | **Pong propio como banco de pruebas** | Un Pong pequeño en pygame que puede correr sin ventana y expone su estado real. Sirve para medir al agente sin depender de juegos de terceros y también como minijuego del gato. | `src/minigames/pong.py` | El test corre 1000 rallies sin ventana en menos de 10 s |
| 2.2 | **Separar el agente en módulos** | Percepción → Estado → Política → Actuador, con un perfil JSON por juego (región de pantalla, detectores, teclas, cómo se ve el marcador). | `src/screen_agent/{perception,state,policy,actuator}.py`, `profiles/*.json` | El POC actual funciona como perfil `pong_generic.json` |
| 2.3 | **Detección sin `cv2`** | Diferencia entre frames con numpy: lo pequeño que se mueve es la pelota y el rectángulo ancho controlado es la paleta. La calibración por color pasa a ser opcional. La pantalla se captura con `mss`. | `perception.py`, `requirements-build.txt` (+`mss`) | Detecta la pelota en el Pong propio el 95 % de los frames, sin calibrar |
| 2.4 | **Predecir dónde cae la pelota** | Velocidad estimada con un promedio móvil de varios frames, simulación de rebotes en las paredes y movimiento al punto de llegada. Un "nivel de error humano" ajustable hace que a veces falle a propósito. | `policy.py` | Tasa de aciertos en el Pong propio: actual ~X % → predicción ≥ 90 % (se mide al empezar 2.1) |
| 2.5 | **Mover sin bloquear** | Mantener la tecla pulsada mientras el error supere la zona muerta y soltarla al llegar, sin `sleep`. | `actuator.py` | El bucle corre a ≥ 30 fps de forma estable |
| 2.6 | **Seguridad** | Solo envía teclas si la ventana del juego tiene el foco; tecla de pánico global (Ctrl+Alt+P); `pyautogui.FAILSAFE`. El agente se activa a mano desde el menú, nunca solo. | `actuator.py`, `desktop.py` | Si cambias de ventana, deja de pulsar en menos de 100 ms |
| 2.7 | **Marcador y recompensa** | Detecta puntos, vidas y fin de partida según el perfil, y cada punto se convierte en una recompensa. | `state.py`, perfiles | Cuenta bien los puntos en el Pong propio |
| 2.8 | **Integrarlo con el gato** | Opción del menú **"Watch me play"**: el gato se sube a la ventana del juego (usa 1.3), mueve la pata cuando mueve la paleta y comenta con `cat_voice` ("¡casi!", "¡te gané!"). Las partidas se guardan en `memory_graph` con `source="screen_game"`: le gustan los juegos donde gana, se frustra un poco (sin enfadarse) en los que pierde, y pide volver a su favorito. | `game.py`, `cat_voice.py`, `cat_brain.py` | Se puede jugar desde el `.exe` y el gato recuerda su juego favorito |
| 2.9 | **Aprende mirándote** | Mientras tú juegas al Pong propio, se graban pares (estado, tecla). Con eso se entrena con numpy una política pequeña (regresión logística o kNN, sin sklearn) que imita tu estilo. Mensaje para el usuario: "tu gato aprendió a jugar como tú". | `policy.py` (`ImitationPolicy`), `data/` | Tras 3 partidas tuyas, juega claramente mejor que al azar y se parece a tu estilo |
| 2.10 | *(Opcional)* RL de verdad | Wrapper de gymnasium con DQN/PPO, solo para experimentar; **no entra en el `.exe`**. | `tools/rl/` | Solo si las tareas 2.4 a 2.9 se quedan cortas |

---

## Fase 3 · v1.3 "Compañero de trabajo" (~1 semana)

**Estado:** tareas 3.1 a 3.4 implementadas en la rama `feature/phase3-companion`. La lógica está en [companion.py](../src/companion.py), que se prueba sin ventana con un reloj y una entrada falsos. Hay 14 tests en [test_companion.py](../test_companion.py), y 3 de ellos usan el juego completo sin ventana.

- **Privacidad:** solo se usan la marca de tiempo de la última entrada (`GetLastInputInfo`) y la posición del cursor. Un test comprueba que `companion.py` no lee teclas ni captura la pantalla.
- **Ritmo al escribir:** cuenta las veces que cambia la marca de tiempo mientras el cursor no se mueve. Así distingue escribir de mover el ratón sin saber qué teclas se pulsan.
- **Ausencia:** las necesidades avanzan 5 veces más despacio, el hambre no sube mientras no estás y la energía se recupera. Un Focus cuenta como presencia, así que al terminar uno leyendo no te marca como ausente de inmediato.
- **Focus:** cero mensajes durante el Focus, verificado con un test de 1 minuto con el gato hambriento y cansado. Al terminar, sube el vínculo, el gato te felicita, te propone una pausa y desbloquea logros (1 y 10 sesiones).
- **Tiempo juntos:** se guarda en la partida y aparece en la tarjeta al pasar el ratón y en Stats. Cada 10 horas hay una pequeña celebración.

| # | Tarea | Detalle | Archivos | Listo cuando… |
|---|---|---|---|---|
| 3.1 | **Ausencia y regreso** | Con `GetLastInputInfo`: si no hay actividad en más de 5 minutos, el gato se duerme. Al volver, te saluda ("¡volviste!") una sola vez. Las necesidades bajan más despacio mientras no estás. | `game.py`, `desktop.py`, `cat_brain.py` | Nunca te recibe con un gato hambriento por haber estado fuera |
| 3.2 | **Modo Focus (pomodoro)** | Menú → "Focus 25 min": el gato se acurruca en un borde y no habla ni pide nada. Al terminar te felicita, sube el vínculo y te propone una pausa con juego. | `game.py`, `cat_voice.py`, `config.py` | Cero mensajes durante el Focus |
| 3.3 | **Ritmo al escribir** (como Bongo Cat, sin keylogger) | Mide solo la intensidad de la actividad (cuántas veces cambia `GetLastInputInfo`, no qué teclas). Si escribes mucho, el gato mueve las patas al ritmo o se pone a tu lado tranquilo. | `desktop.py`, `game.py` | El código no lee ni guarda ninguna tecla |
| 3.4 | **Tiempo juntos** | Contador de horas de compañía que se guarda con la partida. Sirve para los desbloqueos de la Fase 4 y aparece en la tarjeta de Stats. | `cat_brain.py`, `game.py` | El contador sobrevive a guardar y cargar |

---

## Fase 4 · v1.4 "Colección y visitantes" (~1–1.5 semanas)

**Estado:** tareas 4.1 a 4.4 implementadas en la rama `feature/phase4-collection`. La lógica pura está en [collection.py](../src/collection.py) y el dibujo y la integración en `game.py`. Hay 13 tests en [test_collection.py](../test_collection.py), y 2 de ellos usan el juego completo sin ventana.

- **Armario:** 8 accesorios en tres huecos (cabeza, cara y cuello). Cada uno tiene un punto de anclaje por postura y fotograma, se refleja al mirar a la izquierda y algunos tienen una versión de perfil. Se revisaron con una hoja de sprites de todas las posturas. Los requisitos son tiempo juntos, vínculo, sesiones de Focus, logros, el récord de Pong y visitantes conocidos.
- **Visitantes:** como máximo uno al día, guardado en `visitors.json` para que reiniciar el juego no permita otra visita. Solo aparecen si el gato está tranquilo (sin Focus, sin ausencia, sin arcade y sin arrastrarlo) y nunca en los 2 primeros minutos. La visita sigue el orden llegar, olerse, jugar e irse. Hay un límite de 75 s, y si el usuario necesita al gato, el visitante se va.
- **Pelajes:** 8 paletas. `make_cat_sprite` recibe el pelaje y los sprites se guardan en caché por pelaje. Cada gato guarda el suyo (`coat`).
- **Álbum:** visitantes, regalos, récords de Pong (uno por título), logros y desbloqueos, con un máximo de 80 entradas. La tarjeta muestra además la acción favorita según `memory_graph`.
- **Adoptar:** `create_new_cat(name, coat)` amplía el flujo de **New cat** que ya existía. Cada visitante se puede adoptar una sola vez y conserva su pelaje.

| # | Tarea | Detalle | Archivos | Listo cuando… |
|---|---|---|---|---|
| 4.1 | **Armario de cosméticos** | Sombreros, lazos, collares y bufandas en pixel-art de 16×16, dibujados encima del sprite y ajustados a cada postura. Se desbloquean por tiempo juntos, vínculo y logros. Nueva página del menú: "Wardrobe". | `game.py` (`make_accessory_sprite`), `cat_brain.py` | 8 accesorios que se ven bien en todas las posturas, también mirando a la izquierda |
| 4.2 | **Gatos visitantes** | De vez en cuando (máximo uno al día) llega un gato con otro pelaje, generado con `make_cat_sprite` y una paleta distinta. Se huelen, juegan unos minutos y se va. **Nunca hay más de un visitante y nunca se queda.** | `game.py`, `autonomy.py`, `cat_voice.py` | Llega, interactúa, se va, y no se puede acumular |
| 4.3 | **Álbum** | Registro de visitantes, regalos (1.6), récords del Screen Agent y momentos destacados de `memory_graph`. Página del menú "Album". | `game.py`, `memory_graph.py` | El álbum se guarda con la partida |
| 4.4 | **"Adoptar" desde el álbum** *(opcional)* | Un visitante del álbum puede convertirse en gato propio usando el flujo **New cat** que ya existe; no es duplicar al gato. | `game.py` | Usa el flujo existente sin código paralelo |

---

## Orden y dependencias

```
Fase 1 (escritorio) ──► Fase 2 (Screen Agent; 2.8 usa 1.3)
        │
        └──► Fase 3 (trabajo; usa 1.1) ──► Fase 4 (colección; usa 3.4)
```

- **1.1** va primero porque casi todo lo demás depende de él.
- **2.1 a 2.5** no dependen de la Fase 1 y se pueden empezar en paralelo.
- Cada fase es un PR o una serie de PRs y termina con una versión publicada.

## Cómo medimos que va bien

- **Tierno:** en una simulación de 30 minutos, el gato habla como máximo unas 1.5 veces por minuto con el usuario activo y 0 veces en modo Focus.
- **Vivo:** en 30 minutos sin tocarlo, hace al menos 6 acciones distintas, incluidas `perch` y `chase_cursor`.
- **Buen jugador:** ≥ 90 % de aciertos en el Pong propio con la predicción; la política que te imita queda por encima del azar.
- **Ligero:** el `.exe` sigue por debajo de 50 MB y respeta los límites de CPU.
