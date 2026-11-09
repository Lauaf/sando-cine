# 映画館 Sandō · Cine

Aprender japonés con videos de verdad, al estilo de HayaiLearn.

Pegá el link de un video de YouTube en japonés con subtítulos japoneses (aunque sean automáticos) o subí un `.srt`/`.vtt`. La IA separa cada línea en palabras con su lectura y su significado **según el contexto**. Mirás el video, tocás lo que no entendés, lo guardás con ☆ en tu mazo y después lo repasás.

Teclas en la sala: `←`/`→` línea anterior o siguiente, `R` repetir, `Espacio` pausa, `P` pausa automática al final de cada línea, `T` mostrar la traducción, `G` guion completo.

## Cómo correrla

Necesitás Python 3 (solo la biblioteca estándar).

```bash
python server.py            # abre http://127.0.0.1:8772 en el navegador
python server.py --no-abrir --puerto 8772
```

En Windows, `iniciar.pyw` levanta el servidor (o lo reinicia si el código cambió) y abre la app en una ventana de Edge. Cada senda usa su propio puerto, así que podés tener varias abiertas a la vez.

### Controles

Todo se puede usar con mouse, con el teclado (flechas para moverse entre opciones, Enter para elegir, Esc o X para volver) o con un joystick (A elegir, B volver). Arriba: tu nivel y progreso (clic en el nombre), las misiones del día y las opciones.

### Bajar subtítulos de YouTube

Para traer los subtítulos directo desde un link, el servidor usa `yt-dlp` desde un entorno virtual en `venv/` dentro de la carpeta de la app:

```bash
python -m venv venv
venv/Scripts/pip install yt-dlp      # en Windows (en Linux/macOS: venv/bin/pip)
```

Sin ese entorno igual podés subir el archivo de subtítulos a mano.

## Partida y respaldo

El progreso (nivel, racha, misiones del día, logros) se guarda solo en `datos/partida.json` (con una copia por día) y en el navegador. Desde **⚙ Opciones** podés exportar un respaldo y restaurarlo.

Como usa el mismo formato que [Sandō](https://github.com/Lauaf/Sando), podés exportar tu partida desde Sandō y restaurarla acá para seguir con el mismo progreso.

## IA local (opcional)

Si hay un modelo local corriendo, analiza los subtítulos en palabras con su significado en contexto (para ver videos nuevos hace falta la IA). Primero se prueba Qwen (EXL3, puerto 8888) y después Ollama (puerto 11434).

## Relación con Sandō

Esta app es una de las sendas de [Sandō](https://github.com/Lauaf/Sando), el pueblo pixel art donde se practica japonés, piano y café, separada para usarla sola. Es una copia independiente: conserva el historial de commits de sus archivos y desde acá evoluciona por su cuenta.

## Estructura

```
server.py              servidor local: archivos, partida y puente a la IA, videos del cine
iniciar.pyw            lanzador para Windows
web/
  index.html, estilo.css
  js/app.js            arranque de la app
  js/perfil.js         mi progreso: nivel, misiones, últimas dos semanas y logros
  js/progreso.js       XP, niveles, racha, misiones, logros, repaso espaciado y guardado
  js/actividad.js      pantallas (pila con Esc para volver, navegación con flechas)
  js/opciones.js       opciones y respaldo
  js/dialogo.js, js/jp/texto.js, js/ia.js, js/mando.js, js/util.js   piezas compartidas
  js/cine.js           la sala, la cartelera, el mazo y el repaso
  js/japones.js        sesiones de vocabulario (repaso del mazo)
  js/datos/            kana, vocabulario y frases
herramientas/
  subtitulos.py        lee subtítulos de YouTube, .srt y .vtt
```

No hay paso de build ni dependencias de npm: la app son módulos ES servidos tal cual.
