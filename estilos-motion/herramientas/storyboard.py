#!/usr/bin/env python3
"""
storyboard.py · Drop Nation · Skill Motion
Afina un estilo con storyboards: genera varios con la gramática del estilo, los
puntúa contra las referencias y las reglas de retención, y aprende de los aprobados.

Comandos:
  esqueleto <gramatica|estilo.json> --duracion 75 [--n 3] [--partes 3.1,4.2,...] [--variante fiel|dinamica|cine] [--semilla 7] [--salida dir]
      Crea N storyboards nuevos (tiempos, cámara con valores para EI.camara, transiciones,
      eventos y sonidos). Claude completa "que_se_ve" y "texto_voz". Con --partes calza
      los planos con la duración de cada audio de la voz.
  puntuar <gramatica|estilo.json> <sb1.json> [sb2.json ...] [--salida puntaje.md]
      Ranking 0-100 (fidelidad al estilo + retención + movimiento) y qué corregir en cada uno.
      Pásale también los storyboard.json de las referencias para comparar.
  afinar <estilo.json|gramatica.json> <sb_aprobado.json> [--peso 0.3]
      El storyboard aprobado ajusta la gramática "afinada" del estilo (y deja historial).
  md <sb.json>
      Escribe el storyboard como tabla legible (sb.md al lado).

Solo usa la biblioteca estándar de Python.
"""
import argparse, json, math, random, sys, datetime
from pathlib import Path

VERSION = "1.0.0"

# Recetas de la plantilla (assets/estilo.js) para cada pieza del storyboard
RECETA_TRANS = {"corte seco": "EI.corte", "fundido": "EI.fundido", "barrido": "EI.barrido",
                "entrar con zoom": "EI.entrarZoom", "destello": "EI.destello + EI.corte", "paso por negro": "EI.fundido (por #negro)"}
SFX_TRANS = {"corte seco": "impacto", "fundido": "whoosh_corto", "barrido": "whoosh", "entrar con zoom": "whoosh",
             "destello": "brillo", "paso por negro": "whoosh_corto"}
EVENTOS = [  # (tipo, receta, sonido, peso)
    ("etiqueta", "EI.pop(.etiqueta)", "pop", 3), ("globo ícono", "EI.pop(.globo)", "pop", 2),
    ("pulso neón", "EI.neonDibujar + EI.neonPulso", "pulso", 2), ("ondas", "EI.ondas", "pulso", 2),
    ("empujón en palabra clave", "EI.empujon", "tick", 3), ("contador", "EI.contador", "tick", 1),
    ("flecha / círculo que señala", "EI.pop(svg)", "pop", 2), ("partículas que estallan", "EI.particulas", "brillo", 1),
    ("lupa", "EI.lupa", "whoosh_corto", 1), ("transformación del objeto", "tween propio", "whoosh_corto", 2),
]
VARIANTES = {
    "fiel": {"dur": (1.4, 4.8), "mediana": 3.3, "mov_mult": 1.0, "quieto_max": 0.12, "ease": None, "sac_mult": 1.0},
    "dinamica": {"dur": (1.1, 3.6), "mediana": 2.3, "mov_mult": 1.35, "quieto_max": 0.0, "ease": "power2.out", "sac_mult": 1.3},
    "cine": {"dur": (2.2, 5.0), "mediana": 3.8, "mov_mult": 0.8, "quieto_max": 0.05, "ease": "sine.inOut", "sac_mult": 0.5},
}
MOVS = ["acercamiento", "alejamiento", "paneo horizontal", "paneo vertical", "giro", "deriva leve", "quieto"]


# ================================================================ util
def cargar_gramatica(p):
    j = json.loads(Path(p).read_text())
    g = j.get("gramatica", j)
    if "duracion_plano_s" not in g:
        sys.exit("Ese archivo no tiene gramática (corre extraer_estilo.py v2 primero).")
    if g.get("afinada"):  # lo aprendido de storyboards aprobados manda sobre lo medido
        g = {**g, **{k: v for k, v in g["afinada"].items() if k not in ("historial",)}}
    return g, j


def elegir(r, mix, excluir=()):
    items = [(k, v) for k, v in mix.items() if k not in excluir and k not in ("inicio", "—") and v > 0]
    if not items:
        return None
    t = r.random() * sum(v for _, v in items)
    for k, v in items:
        t -= v
        if t <= 0:
            return k
    return items[-1][0]


def cuantil(r, pc, lo=None, hi=None):
    """muestra de una distribución dada por sus percentiles p10..p90"""
    xs = [(0.10, pc["p10"]), (0.25, pc["p25"]), (0.50, pc["p50"]), (0.75, pc["p75"]), (0.90, pc["p90"])]
    u = 0.1 + r.random() * 0.8
    for (a, va), (b, vb) in zip(xs, xs[1:]):
        if u <= b:
            v = va + (vb - va) * (u - a) / (b - a)
            break
    if lo is not None:
        v = max(lo, v)
    if hi is not None:
        v = min(hi, v)
    return v


def normaliza(m):
    s = sum(v for k, v in m.items() if k not in ("inicio", "—")) or 1
    return {k: v / s for k, v in m.items() if k not in ("inicio", "—")}


# ================================================================ esqueleto
def camara(r, mov, dura, g, var):
    z50 = (g.get("zoom_pct_por_plano") or {}).get("p50", 8) or 8
    tasa = min(9.0, max(2.0, z50 / max(1.0, (g["duracion_plano_s"]["p50"] or 4)))) * var["mov_mult"]   # %/s
    z = round(min(0.35, max(0.04, tasa * dura / 100)), 3)
    p50d = g["duracion_plano_s"]["p50"] or 4.0
    pan = round(min(640, max(120, ((g.get("paneo_px_por_plano") or {}).get("p50", 250) or 250) * var["mov_mult"] * dura / p50d)))
    s = 1 if r.random() < 0.5 else -1
    v = {"mov": mov, "escala": [1.0, 1.0], "x_px": [0, 0], "y_px": [0, 0], "giro_grados": [0, 0]}
    if mov == "acercamiento":
        v["escala"] = [1.0, round(1 + z, 3)]; v["y_px"] = [0, round(-z * 300)]
    elif mov == "alejamiento":
        v["escala"] = [round(1 + z, 3), 1.0]
    elif mov == "paneo horizontal":
        v["escala"] = [1.12, 1.12]; v["x_px"] = [s * pan // 2, -s * pan // 2]
    elif mov == "paneo vertical":
        v["escala"] = [1.12, 1.12]; v["y_px"] = [s * pan // 2, -s * pan // 2]
    elif mov == "giro":
        v["escala"] = [1.06, round(1.06 + z / 2, 3)]; v["giro_grados"] = [0, s * round(2 + 3 * r.random(), 1)]
    elif mov == "deriva leve":
        v["escala"] = [1.0, 1.03]; v["y_px"] = [20, -20]
    ease_mix = g.get("easing") or {"sine.inOut": 1}
    v["ease"] = var["ease"] or ({"none": "none"}.get(elegir(r, ease_mix), elegir(r, ease_mix)) or "sine.inOut")
    if v["ease"] == "none" and mov != "quieto":
        v["ease"] = "sine.inOut"   # [mejora] lo lineal se ve robótico en movimientos lentos
    return v


def duraciones(r, total, g, var, partes=None):
    lo, hi = var["dur"]
    # se conserva la FORMA de la distribución del estilo, escalada a la mediana de la variante
    p50 = g["duracion_plano_s"]["p50"] or 4.0
    # (en escala logarítmica y con las colas comprimidas: planos largos se acortan, cortos se respetan)
    def tira(t):
        out, acc = [], 0.0
        while acc < t - 0.01:
            m = cuantil(r, g["duracion_plano_s"])
            d = min(hi, max(lo, var["mediana"] * (max(0.2, m) / p50) ** 0.55))
            if t - acc - d < lo * 0.7:
                d = t - acc
            out.append(round(d, 2)); acc += d
        if len(out) > 1 and out[-1] < lo * 0.6:
            out[-2] = round(out[-2] + out.pop(), 2)
        return out
    def una():
        if partes:
            res = []
            for k, p in enumerate(partes):
                res += [(d, k + 1) for d in tira(p)]
            return res
        return [(d, None) for d in tira(total)]
    # 8 intentos y se queda con el que tiene la mediana más cerca de la de la variante
    cands = [una() for _ in range(8)]
    med = lambda c: sorted(x for x, _ in c)[len(c) // 2]
    return min(cands, key=lambda c: abs(med(c) - var["mediana"]))


def esqueleto(g, total, r, var_nombre, partes=None, titulo="Storyboard"):
    var = VARIANTES[var_nombre]
    durs = duraciones(r, total, g, var, partes)
    # el gancho: primer plano corto (1,2-2,2 s) con algo que pasa antes de 0,8 s
    if durs and durs[0][0] > 2.2:
        resto = round(durs[0][0] - 1.8, 2)
        durs = [(1.8, durs[0][1]), (resto, durs[0][1])] + durs[1:]
    trans_mix = normaliza(g["transiciones"])
    cam_sig = g.get("camara_siguiente") or {}
    cam_mix = normaliza(g["camara"])
    rep_max = min((g.get("mejoras") or {}).get("camara_repite_seguida_max", 0.25), g.get("camara_repite_seguida") or 0.25)
    planos, t, prev_mov, prev_tr, quietos = [], 0.0, None, None, 0
    ev_cada = min(2.0, (g.get("mejoras") or {}).get("evento_cada_s_max", 2.0))
    for n, (d, parte) in enumerate(durs, 1):
        # transición
        if n == 1:
            tr = "inicio"
        else:
            nueva_parte = parte is not None and parte != durs[n - 2][1]
            tr = elegir(r, trans_mix)
            if nueva_parte and r.random() < 0.5:
                tr = r.choice([x for x in ("entrar con zoom", "barrido") if x in trans_mix] or [tr])
            if tr == prev_tr and r.random() < 0.6:
                tr = elegir(r, trans_mix, excluir=(tr,)) or tr
        # cámara (cadena: qué viene después de qué, sin repetir de más)
        mix = normaliza(cam_sig.get(prev_mov, cam_mix)) if prev_mov else cam_mix
        mov = elegir(r, mix) or "acercamiento"
        if mov == "quieto" and (quietos + 1) / max(1, len(durs)) > var["quieto_max"]:
            mov = elegir(r, cam_mix, excluir=("quieto",)) or "deriva leve"
        if n == 1 and mov in ("quieto", "deriva leve"):
            mov = "acercamiento"
        dos_atras = planos[-2]["camara"]["mov"] if len(planos) >= 2 else None
        if mov == prev_mov and (r.random() > rep_max or mov == dos_atras):   # nunca 3 iguales seguidos
            otros = {k: v for k, v in cam_mix.items() if k not in (prev_mov, "quieto")}
            mov = elegir(r, otros) or r.choice([m for m in MOVS if m not in (prev_mov, "quieto")])
        quietos += mov == "quieto"
        cam = camara(r, mov, d, g, var)
        cam["sacudida"] = r.random() < min(0.6, (g.get("sacudida_pct", 20) / 100) * var["sac_mult"] * 0.6)
        # eventos: algo nuevo cada ≤ 2 s
        n_ev = max(0 if d < ev_cada else 1, math.ceil(d / ev_cada) - 1)
        if n == 1:
            n_ev = max(1, n_ev)
        evs = []
        for k in range(n_ev):
            pos = 0.35 if (n == 1 and k == 0) else round((k + 1) * d / (n_ev + 1) + (r.random() - 0.5) * 0.3, 2)
            tipo, receta, son, _ = r.choices(EVENTOS, weights=[e[3] for e in EVENTOS])[0]
            if n == 1 and k == 0:
                tipo, receta, son = "transformación del objeto", "tween propio", "impacto"
            evs.append({"t": round(t + max(0.2, min(d - 0.2, pos)), 2), "tipo": tipo, "receta": receta})
        sfx = []
        if tr != "inicio":
            sfx.append({"t": round(t, 2), "sonido": SFX_TRANS.get(tr, "whoosh")})
        for e in evs:
            son = next((x[2] for x in EVENTOS if x[0] == e["tipo"]), "pop")
            if n == 1 and e is evs[0]:
                son = "impacto"
            sfx.append({"t": e["t"], "sonido": son})
        if cam["sacudida"]:
            sfx.append({"t": round(t + d * 0.5, 2), "sonido": "impacto"})
        planos.append({"n": n, "inicio": round(t, 2), "dura": d, "parte": parte, "transicion_entrada": tr,
                       "receta_transicion": RECETA_TRANS.get(tr, ""), "camara": cam,
                       "receta_camara": receta_camara(n, t, d, cam), "eventos": evs, "sfx": sfx,
                       "texto_voz": "COMPLETAR", "que_se_ve": "COMPLETAR"})
        t += d
        prev_mov, prev_tr = mov, tr
    # sonidos extra hasta la densidad del estilo (ticks en palabras clave)
    objetivo = g.get("sfx_por_min") or 50
    tot = sum(len(p["sfx"]) for p in planos)
    falta = int(objetivo * t / 60) - tot
    for k in range(max(0, falta)):
        p = planos[(k * 3) % len(planos)]
        p["sfx"].append({"t": round(p["inicio"] + p["dura"] * (0.25 + 0.5 * r.random()), 2), "sonido": "tick (palabra clave)"})
    for p in planos:
        p["sfx"].sort(key=lambda s: s["t"])
    return {"titulo": titulo, "tipo": "esqueleto", "variante": var_nombre, "duracion_s": round(t, 2),
            "generado_con": f"storyboard.py v{VERSION}", "planos": planos}


def receta_camara(n, t, d, c):
    desde = {"scale": c["escala"][0], "x": c["x_px"][0], "y": c["y_px"][0], "rotation": c["giro_grados"][0]}
    hasta = {"scale": c["escala"][1], "x": c["x_px"][1], "y": c["y_px"][1], "rotation": c["giro_grados"][1]}
    s = f'EI.camara(tl, "#e{n}-cam", {round(t, 2)}, {d}, {json.dumps(desde)}, {json.dumps(hasta)}, "{c["ease"]}")'
    if c.get("sacudida"):
        s += f'; EI.sacudida(tl, "#e{n}-cam", {round(t + d * 0.5, 2)}, 14, 0.35)'
    return s


# ================================================================ puntaje
def rasgos(sb):
    P = sb["planos"]
    dur = sb.get("duracion_s") or sum(p["dura"] for p in P)
    cnt = lambda f: {k: sum(1 for p in P if f(p) == k) / max(1, len(P)) for k in {f(p) for p in P}}
    movs = [p["camara"].get("mov", "quieto") for p in P]
    trs = [p["transicion_entrada"] for p in P[1:]]
    sfx = [s for p in P for s in p.get("sfx", [])]
    evs = [e for p in P for e in p.get("eventos", [])]
    cortes = [p["inicio"] for p in P[1:]]
    con_golpe = sum(1 for c in cortes if any(abs(s["t"] - c) <= 0.12 for s in sfx))
    cambios = sorted(cortes + [e["t"] for e in evs])
    huecos = [b - a for a, b in zip([0.0] + cambios, cambios + [dur])]
    zooms = [abs((p["camara"].get("escala") or [1, 1])[1] - (p["camara"].get("escala") or [1, 1])[0]) * 100 for p in P]
    racha, mx = 1, 1
    for a, b in zip(movs, movs[1:]):
        racha = racha + 1 if a == b else 1
        mx = max(mx, racha)
    durs = sorted(p["dura"] for p in P)
    return {"n": len(P), "dur": dur, "durs": durs, "mediana": durs[len(durs) // 2] if durs else 0,
            "trans": {k: trs.count(k) / max(1, len(trs)) for k in set(trs)}, "cam": cnt(lambda p: p["camara"].get("mov", "quieto")),
            "ease": cnt(lambda p: p["camara"].get("ease", "—")), "repite": sum(1 for a, b in zip(movs, movs[1:]) if a == b) / max(1, len(movs) - 1),
            "racha_max": mx, "quieto": movs.count("quieto") / max(1, len(movs)), "tipos_cam": len(set(movs) - {"quieto"}),
            "sfx_min": len(sfx) / max(1, dur) * 60, "golpe_corte": 100 * con_golpe / max(1, len(cortes)),
            "evento_cada": dur / (len(cambios) + 1), "hueco_max": max(huecos) if huecos else dur,
            "primer_cambio": min(cambios) if cambios else dur, "primer_corte": cortes[0] if cortes else dur,
            "zoom_med": sorted(zooms)[len(zooms) // 2] if zooms else 0, "sacudida": sum(1 for p in P if p["camara"].get("sacudida")) / max(1, len(P)),
            "movs": movs, "cortes": cortes, "huecos": list(zip([0.0] + cambios, huecos))}


def l1(a, b):
    a, b = normaliza(a), normaliza(b)
    return sum(abs(a.get(k, 0) - b.get(k, 0)) for k in set(a) | set(b))


def puntuar_uno(sb, g):
    R = rasgos(sb)
    gs = {"ease": {("sine.inOut" if k == "none" else k): v for k, v in (g.get("easing") or {}).items()}}
    # fidelidad: lo que hace que "se vea como el estilo"
    d_tr = l1(R["trans"], g["transiciones"]) / 2
    d_cam = l1({k: v for k, v in R["cam"].items()}, g["camara"]) / 2
    d_sfx = min(1, abs(R["sfx_min"] - (g.get("sfx_por_min") or 50)) / max(1, g.get("sfx_por_min") or 50))
    z_ref = (g.get("zoom_pct_por_plano") or {}).get("p50") or 8
    d_zoom = min(1, abs(math.log((R["zoom_med"] + 1) / (min(z_ref, 30) + 1))) / 1.5)
    fid = 100 * (1 - (0.35 * d_tr + 0.35 * d_cam + 0.15 * d_sfx + 0.15 * d_zoom))
    # retención: las reglas [mejora]
    reglas = [
        (R["primer_cambio"] <= 0.8, f"Nada cambia antes de 0,8 s (primer cambio a los {R['primer_cambio']:.1f} s): agrega una transformación en el plano 1.", 15),
        (R["primer_corte"] <= 4.0, f"El primer corte llega a los {R['primer_corte']:.1f} s: corta el gancho antes de los 4 s.", 10),
        (2.0 <= R["mediana"] <= 4.5, f"Plano mediano de {R['mediana']:.1f} s: lleva los planos a 2-4,5 s.", 15),
        (R["hueco_max"] <= 2.6, None, 20),
        (R["golpe_corte"] >= 80, f"Solo el {R['golpe_corte']:.0f}% de los cortes tiene sonido: pon whoosh/impacto en cada corte.", 15),
        (40 <= R["sfx_min"] <= 70, f"{R['sfx_min']:.0f} efectos por minuto: apunta a 40-70.", 10),
        (R["evento_cada"] <= 2.0, f"Algo nuevo pasa cada {R['evento_cada']:.1f} s: baja a ≤ 2 s con eventos (etiqueta, pulso, empujón).", 15),
    ]
    ret, arreglos = 0, []
    for ok, msg, w in reglas:
        ret += w if ok else 0
        if not ok and msg:
            arreglos.append(msg)
    if R["hueco_max"] > 2.6:
        malos = [f"{a:.1f}-{a+h:.1f} s" for a, h in R["huecos"] if h > 2.6][:4]
        arreglos.append("Tramos sin nada nuevo de más de 2,6 s: " + ", ".join(malos) + ".")
    # movimiento de cámara
    mov = 100
    if R["quieto"] > 0.1: mov -= 35; arreglos.append(f"{R['quieto']*100:.0f}% de planos con cámara quieta: dale deriva o empujón.")
    if R["racha_max"] >= 3: mov -= 25; arreglos.append(f"Hay {R['racha_max']} planos seguidos con el mismo movimiento: alterna acercar/alejar/panear.")
    if R["tipos_cam"] < 4: mov -= 25; arreglos.append(f"Solo {R['tipos_cam']} tipos de movimiento: suma paneo, giro o alejamiento.")
    if R["repite"] > 0.3: mov -= 15
    mov = max(0, mov)
    total = round(0.4 * fid + 0.4 * ret + 0.2 * mov, 1)
    if d_tr > 0.35:
        arreglos.append("Las transiciones no se parecen al estilo: usa más " + ", ".join(k for k, _ in sorted(normaliza(g["transiciones"]).items(), key=lambda z: -z[1])[:2]) + ".")
    if d_cam > 0.35:
        arreglos.append("La mezcla de cámara se aleja del estilo: más " + ", ".join(k for k, _ in sorted(normaliza(g["camara"]).items(), key=lambda z: -z[1])[:2]) + ".")
    return {"titulo": sb.get("titulo", "?")[:50], "tipo": sb.get("tipo", ""), "variante": sb.get("variante", ""),
            "total": total, "fidelidad": round(fid, 1), "retencion": ret, "movimiento": mov,
            "planos": R["n"], "plano_mediana_s": round(R["mediana"], 2), "evento_cada_s": round(R["evento_cada"], 2),
            "sfx_por_min": round(R["sfx_min"]), "cortes_con_golpe_pct": round(R["golpe_corte"]), "arreglos": arreglos}


# ================================================================ afinar
def afinar(ruta, sb, peso):
    j = json.loads(Path(ruta).read_text())
    g = j.get("gramatica", j)
    R = rasgos(sb)
    base = g.get("afinada") or {k: g[k] for k in ("transiciones", "camara", "easing", "duracion_plano_s", "sfx_por_min") if k in g}
    mezcla = lambda a, b: {k: round((1 - peso) * normaliza(a).get(k, 0) + peso * normaliza(b).get(k, 0), 3) for k in set(normaliza(a)) | set(normaliza(b))}
    durs = R["durs"]
    q = lambda p: durs[min(len(durs) - 1, int(p * len(durs)))]
    nuevo = {"transiciones": mezcla(base["transiciones"], R["trans"]), "camara": mezcla(base["camara"], R["cam"]),
             "easing": mezcla(base.get("easing", {}), R["ease"]),
             "duracion_plano_s": {f"p{int(p*100)}": round((1 - peso) * base["duracion_plano_s"][f"p{int(p*100)}"] + peso * q(p), 2) for p in (0.10, 0.25, 0.50, 0.75, 0.90)},
             "sfx_por_min": round((1 - peso) * (base.get("sfx_por_min") or 50) + peso * R["sfx_min"], 1)}
    hist = (g.get("afinada") or {}).get("historial", [])
    hist.append({"fecha": datetime.date.today().isoformat(), "storyboard": sb.get("titulo", "?"), "peso": peso})
    nuevo["historial"] = hist
    g["afinada"] = nuevo
    if "gramatica" in j:
        j["gramatica"] = g
        v = j.get("version", "1.0.0").split(".")
        j["version"] = ".".join(v[:2] + [str(int(v[2]) + 1 if len(v) > 2 and v[2].isdigit() else 1)])
    Path(ruta).write_text(json.dumps(j, ensure_ascii=False, indent=1))
    return j.get("version"), len(hist)


# ================================================================ markdown
def md(sb):
    L = [f"# Storyboard · {sb.get('titulo','')}", "", f"{len(sb['planos'])} planos · {sb.get('duracion_s')} s · {sb.get('tipo','')} {sb.get('variante','')}", "",
         "| # | Inicio | Dura | Entra con | Cámara | Eventos | Sonidos | Voz / texto | Qué se ve |", "|---|---|---|---|---|---|---|---|---|"]
    for p in sb["planos"]:
        c = p["camara"]
        cam = c.get("mov", "")
        e = c.get("escala") or [1, 1]
        if abs(e[1] - e[0]) > 0.015: cam += f" {e[0]}→{e[1]}"
        if (c.get("x_px") or [0, 0])[1] != (c.get("x_px") or [0, 0])[0]: cam += f" x{c['x_px'][0]}→{c['x_px'][1]}"
        if (c.get("y_px") or [0, 0])[1] != (c.get("y_px") or [0, 0])[0]: cam += f" y{c['y_px'][0]}→{c['y_px'][1]}"
        if (c.get("giro_grados") or [0, 0])[1]: cam += f" giro {c['giro_grados'][1]}°"
        if c.get("sacudida"): cam += " + sacudida"
        ev = "; ".join(f"{x['t']}s {x['tipo']}" for x in p.get("eventos", []) if x.get("tipo") != "COMPLETAR") or str(len(p.get("eventos", [])))
        so = ", ".join(s["sonido"] for s in p.get("sfx", [])) or "—"
        L.append(f"| {p['n']} | {p['inicio']} | {p['dura']} | {p['transicion_entrada']} | {cam} ({c.get('ease','')}) | {ev} | {so} | {str(p.get('texto_voz',''))[:70]} | {p.get('que_se_ve','')} |")
    return "\n".join(L) + "\n"


# ================================================================ main
def main():
    ap = argparse.ArgumentParser(description="Genera, puntúa y afina storyboards de un estilo.")
    sp = ap.add_subparsers(dest="cmd", required=True)
    a = sp.add_parser("esqueleto"); a.add_argument("gramatica"); a.add_argument("--duracion", type=float, default=75)
    a.add_argument("--n", type=int, default=3); a.add_argument("--partes"); a.add_argument("--variante", choices=list(VARIANTES))
    a.add_argument("--semilla", type=int, default=7); a.add_argument("--salida", default="."); a.add_argument("--titulo", default="Storyboard")
    b = sp.add_parser("puntuar"); b.add_argument("gramatica"); b.add_argument("storyboards", nargs="+"); b.add_argument("--salida")
    c = sp.add_parser("afinar"); c.add_argument("estilo"); c.add_argument("storyboard"); c.add_argument("--peso", type=float, default=0.3)
    d = sp.add_parser("md"); d.add_argument("storyboard")
    x = ap.parse_args()

    if x.cmd == "esqueleto":
        g, _ = cargar_gramatica(x.gramatica)
        partes = [float(v) for v in x.partes.split(",")] if x.partes else None
        total = sum(partes) if partes else x.duracion
        out = Path(x.salida); out.mkdir(parents=True, exist_ok=True)
        orden = [x.variante] * x.n if x.variante else [list(VARIANTES)[k % 3] for k in range(x.n)]
        filas = []
        for k, var in enumerate(orden, 1):
            sb = esqueleto(g, total, random.Random(x.semilla * 100 + k), var, partes, f"{x.titulo} {k} ({var})")
            p = out / f"sb_{k}_{var}.json"
            p.write_text(json.dumps(sb, ensure_ascii=False, indent=1))
            p.with_suffix(".md").write_text(md(sb))
            s = puntuar_uno(sb, g)
            filas.append((p.name, var, len(sb["planos"]), s["total"]))
        print("Storyboards creados (completa 'que_se_ve' y 'texto_voz'):")
        for f in filas:
            print(f"  {f[0]} · {f[1]} · {f[2]} planos · puntaje base {f[3]}")
    elif x.cmd == "puntuar":
        g, _ = cargar_gramatica(x.gramatica)
        res = [puntuar_uno(json.loads(Path(p).read_text()), g) | {"archivo": Path(p).parent.name + "/" + Path(p).name} for p in x.storyboards]
        res.sort(key=lambda z: -z["total"])
        L = ["# Puntaje de storyboards", "", "Total = 40 % fidelidad al estilo + 40 % retención + 20 % movimiento de cámara.", "",
             "| # | Storyboard | Total | Fidelidad | Retención | Movimiento | Planos | Plano mediano | Algo nuevo cada | SFX/min | Cortes con golpe |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for i, r in enumerate(res, 1):
            L.append(f"| {i} | {r['archivo']} {r['variante']} | **{r['total']}** | {r['fidelidad']} | {r['retencion']} | {r['movimiento']} | {r['planos']} | {r['plano_mediana_s']} s | {r['evento_cada_s']} s | {r['sfx_por_min']} | {r['cortes_con_golpe_pct']}% |")
        L += ["", "## Qué corregir", ""]
        for r in res:
            L += [f"**{r['archivo']}** ({r['total']})", ""] + [f"- {m}" for m in r["arreglos"]] + (["- Nada: está listo."] if not r["arreglos"] else []) + [""]
        txt = "\n".join(L)
        print(txt)
        if x.salida:
            Path(x.salida).write_text(txt + "\n")
    elif x.cmd == "afinar":
        sb = json.loads(Path(x.storyboard).read_text())
        v, n = afinar(x.estilo, sb, x.peso)
        print(f"Gramática afinada con '{sb.get('titulo')}' (peso {x.peso}). Aprobados acumulados: {n}." + (f" Versión del estilo: {v}" if v else ""))
    elif x.cmd == "md":
        p = Path(x.storyboard)
        p.with_suffix(".md").write_text(md(json.loads(p.read_text())))
        print("→", p.with_suffix(".md"))


if __name__ == "__main__":
    main()
