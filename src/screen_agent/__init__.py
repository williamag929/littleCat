"""
screen_agent - LittleCat plays paddle games by looking at the screen.

    perception  (pixels -> ball / paddle positions)
        -> state     (positions over time -> velocity, hits, misses, rewards)
        -> policy    (state -> left / stay / right)
        -> actuator  (action -> keys held down, safely)

Each game is described by a JSON profile in screen_agent/profiles/.
Only numpy + ctypes: it ships inside LittleCat.exe.
"""
