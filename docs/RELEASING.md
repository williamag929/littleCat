# Cómo publicar una versión

Cada versión publica un único `LittleCat-vX.Y.Z-windows.exe` en la página de [Releases](https://github.com/williamag929/littleCat/releases). Quien lo descargue no necesita instalar Python.

## Publicar (2 comandos)

```powershell
git tag v1.0.0
git push origin v1.0.0
```

Al subir el tag, GitHub Actions ([.github/workflows/release.yml](../.github/workflows/release.yml)):

1. Instala las dependencias mínimas (`requirements-build.txt`) en Windows.
2. Corre `test_memory_graph.py` como prueba rápida.
3. Compila el `.exe` con PyInstaller (`tools/build_release.py`).
4. Crea el Release con notas generadas a partir de los PRs fusionados desde la versión anterior.

El proceso tarda unos 3–5 minutos. Para seguirlo: pestaña **Actions** del repo, o `gh run watch`.

Sin terminal: **Actions → Release → Run workflow**, con la versión (por ejemplo `v1.0.1`).

## Numeración

- `v1.0.1`: arreglos pequeños.
- `v1.1.0`: funciones nuevas.
- `v2.0.0`: cambios que rompen partidas guardadas.

## Probar el build en tu PC

```powershell
pip install -r requirements-build.txt
python tools/build_release.py v1.0.0-local
# -> dist/LittleCat-v1.0.0-local-windows.exe
```

## Para quien descarga

- Doble clic en el `.exe`. El gato aparece en el escritorio; con clic derecho sobre él se abre el menú, y "Goodnight" guarda y cierra.
- Las partidas se guardan en una carpeta `LittleCat-data` junto al `.exe`. Para conservar los gatos, mueve el `.exe` y esa carpeta juntos.
- Windows SmartScreen puede avisar de que la app no está firmada: **Más información → Ejecutar de todas formas**.
- LARY (el chat con IA) no viene incluido en el `.exe`, para mantenerlo ligero y sin claves.
