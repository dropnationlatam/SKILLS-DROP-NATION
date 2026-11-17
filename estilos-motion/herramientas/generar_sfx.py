#!/usr/bin/env python3
"""
generar_sfx.py · Drop Nation · Skill Motion
Crea por código (sin descargar nada) los efectos de sonido base del estilo:
whoosh (transición), pop (etiqueta/ícono), tick (palabra clave / contador),
impacto (golpe de gancho), brillo (destello), pulso (señal neón), burbuja (CTA).

Uso: python3 generar_sfx.py <carpeta_salida>
"""
import sys, wave
from pathlib import Path
import numpy as np

SR = 44100
rng = np.random.default_rng(7)


def env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / max(r, 1e-4))
    return e


def lp(x, k):  # pasa bajos simple
    if k <= 1:
        return x
    return np.convolve(x, np.ones(k) / k, mode="same")


def save(path, x, gain_db=-3):
    x = x / (np.max(np.abs(x)) + 1e-9) * 10 ** (gain_db / 20)
    s = np.stack([x, x], 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((s * 32767).astype(np.int16).tobytes())


def whoosh(d=0.45):
    n = int(SR * d); t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    # barrido de filtro: suma de pasa-bajos con ventana móvil
    for k, w in ((40, 1 - t), (12, np.sin(np.pi * t)), (4, t ** 2)):
        out += lp(noise, k) * w
    shape = np.sin(np.pi * t) ** 1.5
    return out * shape


def pop(f=900, d=0.12):
    n = int(SR * d); t = np.arange(n) / SR
    f_t = f * (1 + 1.5 * np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f_t) / SR) * env(n, 0.002, 0.035)


def tick(d=0.05):
    n = int(SR * d); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 2400 * t) + 0.5 * rng.standard_normal(n) * np.exp(-t * 400)) * env(n, 0.001, 0.012)


def impacto(d=0.6):
    n = int(SR * d); t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (55 + 90 * np.exp(-t * 25)) * t) * env(n, 0.002, 0.18)
    crack = lp(rng.standard_normal(n), 3) * env(n, 0.001, 0.03)
    return sub + 0.5 * crack


def brillo(d=0.7):
    n = int(SR * d); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t + i) * np.exp(-t * (6 + i * 2)) for i, f in enumerate((1760, 2349, 2637, 3520)))
    return x * env(n, 0.004, 0.25)


def pulso(d=0.35):
    n = int(SR * d); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (300 + 500 * t / d) * t) * np.sin(np.pi * t / d) ** 2 * 0.8


def burbuja(d=0.18):
    n = int(SR * d); t = np.arange(n) / SR
    return np.sin(2 * np.pi * (500 + 900 * t / d) * t) * env(n, 0.003, 0.06)


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "sfx")
    out.mkdir(parents=True, exist_ok=True)
    for name, x, g in [("whoosh", whoosh(), -4), ("whoosh_corto", whoosh(0.25), -5), ("pop", pop(), -6),
                       ("tick", tick(), -9), ("impacto", impacto(), -2), ("brillo", brillo(), -8),
                       ("pulso", pulso(), -9), ("burbuja", burbuja(), -6)]:
        save(out / f"{name}.wav", x, g)
    print("SFX listos en", out)


if __name__ == "__main__":
    main()
