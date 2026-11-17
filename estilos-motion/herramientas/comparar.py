#!/usr/bin/env python3
"""
comparar.py · Drop Nation · Skill Motion
Pone lado a lado una referencia y nuestro video (el "clon") y dice en números
en qué se parecen y en qué no: color, ritmo de cortes, cámara, sonido.

Uso:
    python3 comparar.py <referencia.mp4> <nuestro.mp4> [<salida>]

Deja en <salida>/ (por defecto ./comparacion):
    lado_a_lado.jpg     8 momentos equivalentes: referencia arriba, nuestro abajo
    comparacion.md      tabla con cada medida, la diferencia y si pasa o no
"""
import sys, json
from pathlib import Path
import numpy as np
import cv2

sys.path.insert(0, str(Path(__file__).parent))
import extraer_estilo as X  # noqa: E402


def cuadro(path, t):
    cap = cv2.VideoCapture(str(path))
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, f = cap.read()
    cap.release()
    return f if ok else None


def medir(path, tmp):
    meta = X.probe(path)
    frames, fps = X.pasada_chica(path)
    cuts, destellos, _ = X.detectar_cortes(frames, fps)
    e, zonas = X.energia(frames, fps)
    ev = X.eventos_en_planos(e, zonas, cuts, destellos, fps)
    bounds = [0] + cuts + [len(frames)]
    movs = [X.movimiento(frames, a, b, fps)["principal"] != "quieto" for a, b in zip(bounds, bounds[1:]) if b - a >= 4]
    g = X.grading(frames[:: max(1, int(fps))])
    dur = len(frames) / fps
    Path(tmp).mkdir(parents=True, exist_ok=True)
    au = X.audio(path, [c / fps for c in cuts], dur, Path(tmp)) if meta["tiene_audio"] else None
    durs = np.diff(np.array(bounds) / fps)
    return {"duracion": meta["duracion"], "plano_medio_s": float(np.mean(durs)),
            "cortes_por_min": len(cuts) / max(1, dur) * 60, "evento_cada_s": dur / (len(cuts) + len(ev) + 1),
            "camara_viva_pct": 100 * (sum(movs) / max(1, len(movs))),
            "brillo": g["brillo_medio"], "contraste": g["contraste"], "saturacion": g["saturacion_media"],
            "temperatura": g["temperatura"],
            "golpes_por_min": au["golpes_por_min"] if au else 0,
            "cortes_con_golpe_pct": (au["cortes_con_golpe_pct"] or 0) if au else 0,
            "lufs": au["lufs"] if au else None}


TOL = {  # cuánto puede alejarse nuestro video para considerarse "igual" al estilo
    "brillo": 8, "contraste": 6, "saturacion": 10, "temperatura": 5,
    "camara_viva_pct": 15, "golpes_por_min": 15, "lufs": 2,
}
# medidas donde la guía pide SUPERAR al original (más cortes, planos más cortos, más golpes en cortes)
MEJOR = {"camara_viva_pct": "mayor", "plano_medio_s": "menor", "cortes_por_min": "mayor", "cortes_con_golpe_pct": "mayor", "evento_cada_s": "menor"}


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    ref, nos = Path(sys.argv[1]), Path(sys.argv[2])
    out = Path(sys.argv[3] if len(sys.argv) > 3 else "comparacion"); out.mkdir(parents=True, exist_ok=True)
    (out / "tmp_ref").mkdir(exist_ok=True); (out / "tmp_nos").mkdir(exist_ok=True)
    print("midiendo referencia…"); a = medir(ref, out / "tmp_ref")
    print("midiendo nuestro video…"); b = medir(nos, out / "tmp_nos")

    # hoja lado a lado en 8 momentos proporcionales
    ims_r, ims_n, lab = [], [], []
    for k in range(8):
        p = (k + 0.5) / 8
        fr = cuadro(ref, p * a["duracion"]); fn = cuadro(nos, p * b["duracion"])
        if fr is not None and fn is not None:
            ims_r.append(fr); ims_n.append(fn); lab.append(f"{int(p*100)}%")
    X.hoja(ims_r + ims_n, [f"REF {l}" for l in lab] + [f"NUESTRO {l}" for l in lab], len(lab), out / "lado_a_lado.jpg", w=200)

    filas, pasa_total = [], 0
    for k in ["brillo", "contraste", "saturacion", "temperatura", "camara_viva_pct", "golpes_por_min", "lufs",
              "plano_medio_s", "cortes_por_min", "evento_cada_s", "cortes_con_golpe_pct"]:
        va, vb = a.get(k), b.get(k)
        if va is None or vb is None:
            continue
        if k in MEJOR:
            ok = vb <= va if MEJOR[k] == "menor" else vb >= va
            regla = f"superar ({MEJOR[k]} que la ref.)"
        else:
            ok = abs(vb - va) <= TOL[k]
            regla = f"±{TOL[k]}"
        pasa_total += ok
        filas.append(f"| {k} | {va:.1f} | {vb:.1f} | {vb-va:+.1f} | {regla} | {'✅' if ok else '❌'} |")
    md = ["# Comparación referencia vs nuestro", "", f"Referencia: `{ref.name}` · Nuestro: `{nos.name}`", "",
          "| Medida | Referencia | Nuestro | Diferencia | Regla | ¿Pasa? |", "|---|---|---|---|---|---|"] + filas + [
          "", f"**Pasa {pasa_total} de {len(filas)}.** Mira `lado_a_lado.jpg`: lo que no se mide (trazo, materiales, tipografía) se juzga a ojo.",
          "", "Si algo falla: corrige ese valor en el proyecto, renderiza y vuelve a comparar (máximo 2 vueltas)."]
    (out / "comparacion.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
