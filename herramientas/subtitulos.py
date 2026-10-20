"""Subtítulos japoneses para el cine de Sando.

Uso por consola (en el venv, necesita yt-dlp):
  python subtitulos.py --url <youtube> --salida <json>
Uso como módulo (solo stdlib, lo importa server.py para archivos subidos):
  leer_archivo(nombre, texto) -> [{a, b, t}]
Salida: {titulo, video, canal, duracion, auto, fuente_trad, lineas: [{a, b, t, es?}]}
"""
import argparse
import html
import json
import re
from pathlib import Path


# ---------- parsers ----------
def _seg(ts):
    """'00:01:02.500' / '01:02,5' -> segundos"""
    p = ts.strip().replace(',', '.').split(':')
    s = 0.0
    for x in p:
        s = s * 60 + float(x)
    return s


def _limpiar(t):
    t = re.sub(r'<[^>]+>', '', t)          # etiquetas vtt/srt (<c>, <i>, <00:00:01.000>)
    t = re.sub(r'\{\\[^}]*\}', '', t)      # etiquetas ass
    t = html.unescape(t).replace('​', '')
    return re.sub(r'\s+', ' ', t).strip()


def leer_vtt_srt(texto):
    lineas = []
    bloques = re.split(r'\n\s*\n', texto.replace('\r', ''))
    for b in bloques:
        filas = b.strip().split('\n')
        for k, f in enumerate(filas):
            m = re.match(r'\s*([\d:.,]+)\s*-->\s*([\d:.,]+)', f)
            if m:
                t = _limpiar(' '.join(filas[k + 1:]))
                if t:
                    lineas.append({'a': _seg(m.group(1)), 'b': _seg(m.group(2)), 't': t})
                break
    return lineas


def leer_json3(datos):
    lineas = []
    for ev in datos.get('events', []):
        if 'segs' not in ev:
            continue
        t = _limpiar(''.join(s.get('utf8', '') for s in ev['segs']))
        if not t:
            continue
        a = ev.get('tStartMs', 0) / 1000
        lineas.append({'a': a, 'b': a + ev.get('dDurationMs', 0) / 1000, 't': t})
    return lineas


def ordenar(lineas, auto=False):
    """Ordena, saca repetidas, evita solapes y (en subtítulos automáticos) junta fragmentos cortos."""
    lineas = sorted(lineas, key=lambda x: x['a'])
    sin_rep = []
    for ln in lineas:
        if sin_rep and ln['t'] == sin_rep[-1]['t'] and ln['a'] - sin_rep[-1]['b'] < 0.5:
            sin_rep[-1]['b'] = max(sin_rep[-1]['b'], ln['b'])
            continue
        sin_rep.append(dict(ln))
    if auto:
        juntas = []
        for ln in sin_rep:
            prev = juntas[-1] if juntas else None
            if prev and len(prev['t']) + len(ln['t']) <= 22 and ln['a'] - prev['b'] < 0.6:
                prev['t'] += ln['t'] if re.match(r'[　-鿿]', ln['t']) else ' ' + ln['t']
                prev['b'] = ln['b']
            else:
                juntas.append(ln)
        sin_rep = juntas
    for i, ln in enumerate(sin_rep):
        if i + 1 < len(sin_rep):
            ln['b'] = min(ln['b'], sin_rep[i + 1]['a']) if ln['b'] > ln['a'] else sin_rep[i + 1]['a']
        if ln['b'] <= ln['a']:
            ln['b'] = ln['a'] + 2
        ln['a'], ln['b'] = round(ln['a'], 2), round(ln['b'], 2)
    return sin_rep


def leer_archivo(nombre, texto):
    if nombre.lower().endswith('.json'):
        return ordenar(leer_json3(json.loads(texto)))
    return ordenar(leer_vtt_srt(texto))


def alinear(lineas, trad):
    """Le pone a cada línea japonesa la traducción que más se le superpone en el tiempo."""
    for ln in lineas:
        partes = []
        for tr in trad:
            solape = min(ln['b'], tr['b']) - max(ln['a'], tr['a'])
            if solape > 0 and solape >= 0.5 * min(tr['b'] - tr['a'], ln['b'] - ln['a']):
                partes.append(tr['t'])
        if partes:
            ln['es'] = ' '.join(dict.fromkeys(partes))
    return lineas


# ---------- YouTube ----------
def _elegir(pistas, claves):
    for k in claves:
        for idioma, formatos in pistas.items():
            if idioma == k or (k.endswith('*') and idioma.startswith(k[:-1])):
                por_ext = {f.get('ext'): f for f in formatos}
                f = por_ext.get('json3') or por_ext.get('vtt') or por_ext.get('srt')
                if f:
                    return idioma, f
    return None, None


def bajar(ydl, formato):
    txt = ydl.urlopen(formato['url']).read().decode('utf-8', 'replace')
    return leer_json3(json.loads(txt)) if formato.get('ext') == 'json3' else leer_vtt_srt(txt)


def de_youtube(url):
    import yt_dlp
    with yt_dlp.YoutubeDL({'skip_download': True, 'quiet': True, 'no_warnings': True, 'noplaylist': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        manual = info.get('subtitles') or {}
        auto = info.get('automatic_captions') or {}
        idioma, f = _elegir(manual, ['ja', 'ja*'])
        es_auto = False
        if not f:
            idioma, f = _elegir(auto, ['ja-orig', 'ja', 'ja*'])
            es_auto = True
        if not f:
            raise RuntimeError('Este video no tiene subtítulos en japonés (ni automáticos).')
        lineas = ordenar(bajar(ydl, f), auto=es_auto)
        fuente_trad = None
        for pistas, claves, nombre in ((manual, ['es*'], 'es'), (manual, ['en*'], 'en'), (auto, ['es'], 'es-auto')):
            _, ft = _elegir(pistas, claves)
            if ft:
                try:
                    alinear(lineas, ordenar(bajar(ydl, ft)))
                    fuente_trad = nombre
                    break
                except Exception:
                    pass
    return {
        'titulo': info.get('title') or 'Video', 'video': info.get('id'), 'canal': info.get('uploader') or '',
        'duracion': info.get('duration') or 0, 'auto': es_auto, 'idioma': idioma,
        'fuente_trad': fuente_trad, 'lineas': lineas,
    }


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', required=True)
    ap.add_argument('--salida', required=True)
    a = ap.parse_args()
    try:
        res = de_youtube(a.url)
    except Exception as e:
        res = {'error': str(e)}
    Path(a.salida).write_text(json.dumps(res, ensure_ascii=False), encoding='utf-8')
