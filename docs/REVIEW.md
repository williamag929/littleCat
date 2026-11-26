# LittleCat — Revisión general, memoria y autonomía

Fecha: 2026-11-26 · Alcance: `src/`, `data/`, tests y docs del repo.

## 1. Mapa del proyecto

Grafo completo en [graph/PROJECT_GRAPH.md](graph/PROJECT_GRAPH.md) y [graph/project_graph.json](graph/project_graph.json), regenerable con `python tools/graphify.py`. Tiene 9 módulos, 11 clases, 169 funciones y métodos, y 416 relaciones.

| Módulo | Rol | Notas |
|---|---|---|
| `game.py` (2.4k LOC) | Bucle pygame, render, input, overlay de escritorio, perfiles, sonido, logros, minijuegos, LARY | Concentra el 50 % del código. `update()` tiene 200 líneas y `handle_input()` 180. |
| `cat_brain.py` | Estado emocional, pesos de conducta, Q-learning, guardado | Ahora delega en `memory_graph` y `autonomy`. |
| `memory_graph.py` (nuevo) | Memoria asociativa en JSON | Ver §3. |
| `autonomy.py` (nuevo) | Utility AI por necesidades | Ver §5. |
| `ui_agent.py` | Mensajes, pistas y burbuja de pensamiento | Reglas fijas sobre umbrales. |
| `chat_agent.py` | LARY (OpenAI + captura de pantalla) | |
| `trainer.py`, `screen_agent_poc.py` | Simulación de entrenamiento y PoC aparte | `screen_agent_poc` no está conectado al juego. |

## 2. Hallazgos técnicos

| # | Severidad | Hallazgo | Dónde |
|---|---|---|---|
| T1 | Alta | **El gato se recompensaba a sí mismo.** `auto_perform_action` llamaba a `learn_from_interaction` con la misma recompensa que una acción del jugador. 14 de los 20 recuerdos de Whiskers son acciones propias, y los pesos `play/sleep/eat/rest` estaban saturados en 1.0. **Arreglado:** las acciones con `source="self"` aprenden al 30 %. | `game.py` `auto_perform_action`, `cat_brain.py` |
| T2 | Alta | **El reloj es mucho más rápido de lo que dice `config.py`.** `game.py` fija `GAME_SPEED = 0.02` y no lee el `0.005` de config. Resultado a 30 FPS: el hambre pasa de 0 a 100 en unos 110 s, la energía de 70 a 0 en unos 58 s, y el gato es adulto tras unas 2.2 h de juego. | `game.py:38` |
| T3 | Media | **Q-learning con muy poca señal.** El estado se discretiza en 4⁴×contexto, pero con valores saturados casi siempre cae en el mismo bin (en la prueba, 5 decisiones dieron 1 solo estado). Además la recompensa se asigna a la acción *anterior*. **Mitigado:** ahora solo suma un bonus de ±0.15 sobre la utilidad y ya no anula las necesidades. | `cat_brain.py` `_update_q` |
| T4 | Media | `Whiskers.json` tiene `q_table: {}` con 466 días de edad. Ese guardado es anterior al arreglo de `eval`/`json.loads` (a8e1038); el código actual sí persiste la tabla. | `data/cats/Whiskers.json` |
| T5 | Media | **`.env` está versionado** aunque figura en `.gitignore`. Parece contener un valor de ejemplo (`sk-y…`, 20 caracteres), pero conviene ejecutar `git rm --cached .env` y rotar la clave si alguna vez fue real. | raíz |
| T6 | Baja | En `requirements.txt` faltan `openai`, `Pillow` y `python-dotenv`. Sobra `scikit-learn`, que `src/` no usa. | `requirements.txt` |
| T7 | Baja | `config.py` imprime al importarse y solo se lee parcialmente: el fallback de `CHAT_MODEL` es `gpt-4-vision-preview` en game.py y `gpt-4o` en config. | `config.py`, `game.py:41-76` |
| T8 | Baja | Hay unos 20 `.md/.txt` en la raíz (LARY-*, IMPLEMENTATION-*, *_SUMMARY), así que no está claro cuál es la fuente de verdad. | raíz |

## 3. Memoria: antes y después

**Antes:** una `deque` de 100 dicts `{timestamp, action, response, reward, age}`, de la que se guardaban solo los 20 últimos. No tenía relaciones, no distinguía quién actuó y no influía en las decisiones: era un log.

**Ahora (`littlecat.memory/v1`):** un grafo serializable a JSON que se guarda en la clave `memory_graph` del mismo archivo del gato. Los guardados antiguos se migran solos al cargarlos (`from_legacy`).

```jsonc
{
  "schema": "littlecat.memory/v1",
  "nodes": [ { "id": "action:eat", "type": "action", "count": 7, "valence": 0.72, "first_age": 463.8, "last_age": 468.4 } ],
  "edges": [ { "id": "state:hunger:high|in_state|action:eat", "from": "state:hunger:high", "rel": "in_state",
               "to": "action:eat", "strength": 0.56, "valence": 0.81, "count": 5, "last_age": 468.4 } ],
  "episodes": [ { "id": "ep_000016", "action": "play", "source": "player", "context": "human_nearby",
                  "response": "Played with Ball 🔴", "reward": 0.5, "state": {"hunger": 40.2},
                  "tags": ["hunger:mid", "stimulus:ball"], "links": ["action:play", "source:player", "stimulus:ball"],
                  "prev": "ep_000015", "salience": 0.75 } ]
}
```

- **Tipos de nodo:** `action`, `source` (player/self), `state` (p. ej. `hunger:high`), `context`, `stimulus` (ball, fish, mouse, bird, food, brush, voice, mini_game).
- **Relaciones:** `in_state` (qué ayuda cuando…), `in_context`, `rewarded_by` (quién me hizo sentir bien), `involves` (juguete), `followed_by` (hábitos y secuencias).
- **Aprendizaje:** refuerzo hebbiano de `strength`, media móvil exponencial de `valence`, olvido con vida media de 30 días de juego, poda de aristas débiles, y una consolidación que olvida primero los episodios menos salientes (los emocionales y los primeros se conservan).
- **Consultas:** `expectation(action, tags, context)`, `habit_after(action)`, `favorites(type)`, `recall(tag)`, `neighbors(node, rel)`.
- Ejemplo real convertido: [graph/memory_graph_Whiskers.example.json](graph/memory_graph_Whiskers.example.json). Sus estímulos favoritos son `food` (0.72), `brush` y `ball`, y después de jugar suele comer.

## 4. Crítica de diseño (UX y game design)

**Lo que funciona:** el overlay de escritorio con sprite pixel-art es un formato con mucho encanto (estilo Neko/Shimeji). El menú radial, el cambio de conducta por edad (de cachorro que persigue el cursor a adulto que se queda en su sitio), la curiosidad que lo hace detenerse y los minijuegos de caza le dan una base de "ser vivo" que pocos proyectos tienen.

**Problemas, por orden de impacto:**

1. **El bucle de cuidado se contradice.** Las necesidades caen en 1–2 minutos (T2) y el gato se alimenta solo (`auto eat` resta 30 de hambre sin comida). El jugador recibe avisos constantes, pero su ayuda no es necesaria. *Propuesta:* bajar el ritmo entre 10 y 20 veces y hacer que el gato **pida** (maúlle, camine hacia el cuenco) en lugar de resolverlo solo. Puede comer por su cuenta solo de un cuenco que el jugador haya llenado, porque la comida es un recurso.
2. **Demasiadas voces a la vez.** `agent_message`, `agent_hint`, `agent_suggestion`, la "personality insight" cada 30 s, los recordatorios, la burbuja y LARY compiten por el mismo espacio. *Propuesta:* un único canal con prioridades (necesidad crítica > logro > intención del gato > pista) y un enfriamiento global.
3. **La burbuja parpadea.** `get_thought_bubble()` hace un `random.choice` en cada frame (30 Hz) cuando el gato no está actuando. *Propuesta:* renovarla cada 4–6 s. Ahora, cuando el gato actúa por su cuenta, la burbuja muestra su intención ("so hungry...", "wanna play!"), que es estable y tiene significado.
4. **Una promesa que el sistema no cumple.** La pista dice "My personality develops based on how you treat me", pero la personalidad es un hash MD5 del nombre y no cambia nunca. Whiskers tiene `social = 0.09` y `trust = 100`. *Propuesta:* deriva lenta de los rasgos a partir de la memoria (ver §5).
5. **Atajos poco descubribles.** Y = hablar, N = entrenar, T = acariciar, E = guardar (aunque la pista dice "export"). *Propuesta:* que el menú radial sea la vía principal y muestre la tecla junto a cada icono.
6. **El ciclo de vida es demasiado corto.** Pasa a adulto a los 199 días de juego, unas 2 h reales. La transición más bonita del juego ocurre en la primera sesión.

## 5. Autonomía: técnicas de IA de videojuegos aplicadas

**Ya implementado (`src/autonomy.py`), Utility AI al estilo *The Sims*:**

- Curvas de respuesta logísticas por necesidad (hambre → comer, cansancio → dormir o descansar, aburrimiento → jugar, soledad → ronronear o hablar, desconfianza → esconderse).
- **Ritmo circadiano real:** los gatos son crepusculares, así que tiene más actividad al amanecer (~6:30) y al anochecer (~19:00) y más siesta a mediodía, según la hora del PC.
- **Penalización por aburrimiento:** repetir la misma acción reduce su atractivo (×0.75 por repetición), excepto comer y dormir.
- **Memoria:** `expectation()` sube o baja la utilidad según lo que el gato aprendió en esa situación.
- Selección softmax (impredecible, pero coherente) y una **razón legible** que se muestra en la burbuja.
- Los pesos aprendidos y el Q-learning ahora *matizan* la decisión en lugar de dominarla.

**Siguientes pasos recomendados, por valor y esfuerzo:**

1. **Ajustar el ritmo (T2):** mover `GAME_SPEED` a config y probar 0.002–0.004. Es el cambio de mayor impacto en la experiencia.
2. **Rasgos que evolucionan:** cada día de juego, desplazar `personality` un 1–2 % hacia lo que la memoria refuerza (por ejemplo, mucha interacción `talk` positiva sube `social`). Eso cumple la promesa del punto 4.
3. **Objetos inteligentes (*smart objects*, como en The Sims):** el cuenco, la cama y el rascador anuncian qué necesidad satisfacen, y el gato camina hasta ellos. Así el comportamiento autónomo se ve en pantalla en vez de ser un cambio de números.
4. **Una FSM o behavior tree ligero encima de la utilidad:** estados `Wander → Approach(obj) → Act → Cooldown` con animación y duración propias. Por ejemplo, ahora "sleep" dura 2.5 s.
5. **Iniciativa social:** si `expectation("talk", context=human_nearby)` es alta y el usuario lleva un rato sin interactuar, el gato se acerca al cursor y maúlla. Si el usuario está ocupado (`is_busy`), respeta su espacio.
6. **Recuerdos que se notan:** usar `favorites("stimulus")` para que pida su juguete favorito ("ball?") y `recall()` para reacciones del tipo "la última vez que me escondí no me gustó".

## 6. Cambios en esta revisión

- Nuevos: `src/memory_graph.py`, `src/autonomy.py`, `tools/graphify.py`, `test_memory_graph.py` (10 tests), `docs/graph/*`, este documento.
- `cat_brain.py`: `learn_from_interaction(..., source, context)`, decisión por Utility AI, `memory_graph` en save/load con migración automática y `intent` en `get_status()`.
- `game.py`: marca cada acción como `player` o `self` y la burbuja muestra la intención del gato.
- Ejecutados y en verde: `test_memory_graph.py`, `test_system.py`, `test_ui_agent.py`, `test_game_demo.py` y `test_lary_agent.py`.

## 7. Segunda iteración: una mascota adorable, no estresante

- **Reloj:** `GAME_SPEED` ahora vive en `config.py` y vale 0.0025 (antes 0.02 fijo en el código). El hambre se llena en unos 15 min, la energía se agota en unos 10 min y el gato es adulto tras unas 18 h de juego.
- **Una sola voz:** desaparecen las etiquetas apiladas en la esquina superior izquierda y en el centro. Todo pasa por `say()`: un único globo sobre el gato, con prioridades (celebración > necesidad > respuesta > charla) y enfriamientos. Si llevas 20 s sin tocar nada, el gato no hace charla y espera 3 veces más antes de pedir algo. En la simulación quedan unas 1.5 frases por minuto con el usuario activo y 3 en 5 minutos con el usuario ocupado.
- **Voz del gato (`src/cat_voice.py`):** frases cortas y gatunas ("mrrp... snack? 🐟", "*slow blink* 😌"). Pide las cosas con cariño, sin culpar ("Please don't forget about me" ya no aparece). Los gatos sociales maúllan más. También recuerda su juguete favorito ("ball again? 🔴").
- **Emojis:** la fuente por defecto de pygame los dibujaba como cajas vacías. Los globos ahora usan Segoe UI Emoji, que los muestra en color.
- **Hover:** al pasar el ratón 0.35 s sobre el gato aparece una tarjeta con su nombre y estado de ánimo y barras de Health, Happy, Tummy, Energy y Bond. Además saluda, como mucho una vez cada 40 s.
- **Burbuja de pensamiento:** se mantiene 6 s en lugar de cambiar en cada frame y solo aparece a ratos.
- **Minijuego:** fallar ya no quita felicidad; el gato responde con una frase graciosa ("so close! 😹").
- **Sin etiquetas técnicas:** se eliminaron WALK, SLEEP y SIT sobre el gato, el "Mau Mau" y el "?"/"!" de curiosidad. Ahora la pose comunica la acción y las palabras van en el globo.
- **Menú radial (clic derecho):** un anillo de botones redondos color crema con iconos emoji alrededor del gato, que se queda quieto mientras el menú está abierto. Tiene tres páginas: Cuidados (Pet, Feed, Play, Groom, Talk, Train, Nap, More), Juguetes (Ball, Fish, Mouse, Bird) y More (perfiles, guardar, exportar, LARY, salir). El nombre del botón aparece en una píldora al pasar el ratón y el menú se abre con una animación de 150 ms. No usa transparencias, que sobre el color clave del overlay se veían como un halo violeta.
