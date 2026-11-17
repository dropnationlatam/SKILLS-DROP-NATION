/* ================================================================
   ESTILO "EXPLICADOR ILUSTRADO" · recetas de animación (GSAP)
   Cada función agrega tweens a un timeline pausado de HyperFrames.
   Los tiempos por defecto salen de estilo.json; ajústalos solo si la
   guía de estilo lo dice.
   ================================================================ */
(function () {
  const E = {};

  /* número pseudoaleatorio con semilla (HyperFrames no permite Math.random) */
  E.azar = function (semilla) {
    let s = semilla >>> 0 || 1;
    return function () { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
  };

  /* ---------------- CÁMARA ----------------
     Movimiento lento y continuo dentro del plano (el estilo casi nunca está quieto).
     desde/hasta: { scale, x, y, rotation }  ·  ease por defecto "sine.inOut"            */
  E.camara = function (tl, sel, inicio, dura, desde, hasta, ease) {
    tl.fromTo(sel, Object.assign({ scale: 1, x: 0, y: 0, rotation: 0 }, desde),
      Object.assign({ scale: 1, x: 0, y: 0, rotation: 0, duration: dura, ease: ease || "sine.inOut" }, hasta), inicio);
  };

  /* empujón rápido (punch in) para remarcar una palabra: +6 % en 0,18 s y se asienta */
  E.empujon = function (tl, sel, t, cuanto) {
    const c = cuanto || 0.06;
    tl.to(sel, { scale: "+=" + c, duration: 0.18, ease: "power3.out" }, t)
      .to(sel, { scale: "-=" + c * 0.6, duration: 0.5, ease: "sine.inOut" }, t + 0.18);
  };

  /* sacudida corta y determinista */
  E.sacudida = function (tl, sel, t, fuerza, dura) {
    const f = fuerza || 14, d = dura || 0.35, n = 7, r = E.azar(Math.round(t * 1000));
    for (let i = 0; i < n; i++) {
      const k = 1 - i / n;
      tl.to(sel, { x: "+=" + ((r() - 0.5) * 2 * f * k), y: "+=" + ((r() - 0.5) * 2 * f * k), duration: d / n, ease: "none" }, t + (i * d) / n);
    }
  };

  /* ---------------- TRANSICIONES ---------------- */
  /* barrido: la escena que sale se va desenfocada hacia un lado y la que entra llega del otro */
  E.barrido = function (tl, sale, entra, t, dir) {
    const s = dir === "izq" ? -1 : 1, d = 0.22;
    tl.to(sale, { x: -380 * s, filter: "blur(22px)", opacity: 0, duration: d, ease: "power2.in" }, t - d)
      .fromTo(entra, { x: 380 * s, filter: "blur(22px)", opacity: 0 }, { x: 0, filter: "blur(0px)", opacity: 1, duration: d + 0.08, ease: "power3.out" }, t);
  };

  /* zoom de transición: se "entra" en un punto de la escena (al cuerpo, a la pantalla…) */
  E.entrarZoom = function (tl, sale, entra, t, origen) {
    tl.to(sale, { scale: 3.2, filter: "blur(14px)", opacity: 0, duration: 0.45, ease: "power3.in", transformOrigin: origen || "50% 50%" }, t - 0.45)
      .fromTo(entra, { scale: 0.7, opacity: 0, filter: "blur(10px)" }, { scale: 1, opacity: 1, filter: "blur(0px)", duration: 0.55, ease: "power3.out" }, t - 0.1);
  };

  /* fundido cruzado suave (el más usado en las referencias junto al corte seco) */
  E.fundido = function (tl, sale, entra, t, d) {
    const dd = d || 0.35;
    tl.to(sale, { opacity: 0, duration: dd, ease: "sine.inOut" }, t - dd / 2)
      .fromTo(entra, { opacity: 0 }, { opacity: 1, duration: dd, ease: "sine.inOut" }, t - dd / 2);
  };

  /* corte seco: una escena se apaga y otra se prende en el mismo cuadro */
  E.corte = function (tl, sale, entra, t) {
    tl.set(sale, { opacity: 0 }, t).set(entra, { opacity: 1 }, t);
  };

  /* destello a blanco (paso de tiempo, revelación) */
  E.destello = function (tl, t, fuerza) {
    tl.fromTo("#destello", { opacity: 0 }, { opacity: fuerza || 0.85, duration: 0.06, ease: "none" }, t)
      .to("#destello", { opacity: 0, duration: 0.28, ease: "power2.out" }, t + 0.06);
  };

  /* ---------------- SUBTÍTULOS KARAOKE ----------------
     palabras: [{ p: "texto", i: inicio, f: fin, clave: true? }]
     La frase se va armando palabra por palabra: la palabra que suena entra en blanco,
     las ya dichas bajan a gris; la palabra clave lleva la caja azul con manijas.
     Corta el grupo al final de frase (.,?!:) o a las 6 palabras.                         */
  E.karaoke = function (tl, contenedor, palabras, opciones) {
    const op = Object.assign({ max: 6, dim: "#8E8C9A", tinta: "#FFFFFF" }, opciones || {});
    const cont = document.querySelector(contenedor);
    const grupos = [];
    let g = [];
    palabras.forEach(function (w, k) {
      g.push(w);
      const fin = /[.?!:;]$/.test(w.p) || g.length >= op.max || k === palabras.length - 1 ||
        (palabras[k + 1] && palabras[k + 1].i - w.f > 0.35);
      if (fin) { grupos.push(g); g = []; }
    });
    grupos.forEach(function (grp, gi) {
      const div = document.createElement("div");
      div.className = "grupo";
      div.id = "grupo-" + gi;
      cont.appendChild(div);
      const inicio = grp[0].i, final = (grupos[gi + 1] ? Math.min(grupos[gi + 1][0].i, grp[grp.length - 1].f + 0.6) : grp[grp.length - 1].f + 0.6);
      tl.set(div, { opacity: 1, visibility: "visible" }, Math.max(0.05, inicio - 0.02));
      let anterior = null;
      grp.forEach(function (w, wi) {
        const s = document.createElement("span");
        s.className = "pal" + (w.clave ? " clave" : "");
        s.textContent = w.p;
        if (w.clave) { const c = document.createElement("i"); c.className = "caja"; s.appendChild(c); }
        div.appendChild(s);
        div.appendChild(document.createTextNode(" "));
        tl.fromTo(s, { opacity: 0, y: 10, scale: 0.92 }, { opacity: 1, y: 0, scale: 1, duration: 0.12, ease: "power3.out" }, w.i);
        if (w.clave) tl.fromTo(s.querySelector(".caja"), { opacity: 0, scale: 0.85 }, { opacity: 1, scale: 1, duration: 0.14, ease: "back.out(2)" }, w.i);
        if (anterior) {
          tl.to(anterior, { color: op.dim, duration: 0.08, ease: "none" }, w.i);
          if (anterior.querySelector(".caja")) tl.to(anterior.querySelector(".caja"), { opacity: 0, duration: 0.1 }, w.i);
        }
        anterior = s;
      });
      tl.to(div, { opacity: 0, duration: 0.1, ease: "power2.in" }, final - 0.1);
      tl.set(div, { opacity: 0, visibility: "hidden" }, final);
    });
  };

  /* ---------------- RECURSOS ---------------- */
  /* aparece con rebote (etiquetas, globos, íconos, burbuja) */
  E.pop = function (tl, sel, t, dura) {
    tl.fromTo(sel, { scale: 0.4, opacity: 0, y: 20 }, { scale: 1, opacity: 1, y: 0, duration: 0.32, ease: "back.out(2.2)" }, t);
    if (dura) tl.to(sel, { scale: 0.6, opacity: 0, duration: 0.18, ease: "power2.in" }, t + dura);
  };

  /* línea neón que se dibuja y luego lleva pulsos de luz que viajan (nervios, señales, cables) */
  E.neonDibujar = function (tl, sel, t, dura) {
    document.querySelectorAll(sel).forEach(function (p) {
      const L = p.getTotalLength();
      p.style.strokeDasharray = L + " " + L;
      tl.fromTo(p, { strokeDashoffset: L }, { strokeDashoffset: 0, duration: dura || 0.8, ease: "power2.inOut" }, t);
    });
  };
  /* el camino queda dibujado tenue y una copia brillante viaja encima */
  E.neonPulso = function (tl, sel, t, veces, cada, largo) {
    document.querySelectorAll(sel).forEach(function (base, bi) {
      const p = base.cloneNode(false);
      p.removeAttribute("class");
      p.setAttribute("stroke", "#FFFFFF");
      p.setAttribute("stroke-width", (parseFloat(base.getAttribute("stroke-width")) || 10) * 1.25);
      base.parentNode.appendChild(p);
      tl.to(base, { opacity: 0.55, duration: 0.3 }, t);
      const L = p.getTotalLength(), seg = largo || 120;
      p.style.strokeDasharray = seg + " " + (L + seg);
      p.style.strokeDashoffset = seg;
      const t0 = t + bi * 0.17;
      for (let k = 0; k < (veces || 3); k++) {
        tl.fromTo(p, { strokeDashoffset: seg, opacity: 1 }, { strokeDashoffset: -L, duration: cada || 0.9, ease: "none" }, t0 + k * (cada || 0.9));
      }
    });
  };

  /* ondas concéntricas que se expanden (wifi, sonido, dolor, calor) */
  E.ondas = function (tl, sel, t, veces, cada) {
    const anillos = document.querySelectorAll(sel);
    anillos.forEach(function (a, i) {
      for (let k = 0; k < (veces || 3); k++) {
        const o = a.getAttribute("cx") ? a.getAttribute("cx") + " " + a.getAttribute("cy") : null;
        const org = o ? { svgOrigin: o } : { transformOrigin: "50% 50%" };
        if (k === 0) tl.set(a, Object.assign({ scale: 0.15, opacity: 0 }, org), 0);
        tl.fromTo(a, Object.assign({ scale: 0.15, opacity: 0.95 }, org), Object.assign({ scale: 1, opacity: 0, duration: 1.4, ease: "sine.out", immediateRender: false }, org),
          t + k * (cada || 1.2) + i * 0.35);
      }
    });
  };

  /* partículas que flotan y titilan durante todo el plano (bokeh, polvo, células) */
  E.particulas = function (tl, contenedor, n, t, dura, semilla, color) {
    const c = document.querySelector(contenedor), r = E.azar(semilla || 11);
    for (let i = 0; i < n; i++) {
      const d = document.createElement("div"), sz = 6 + r() * 38;
      d.className = "particula";
      d.style.width = d.style.height = sz + "px";
      d.style.left = (r() * 100) + "%";
      d.style.top = (r() * 100) + "%";
      if (color) d.style.background = "radial-gradient(circle, " + color + ", rgba(0,0,0,0) 70%)";
      c.appendChild(d);
      tl.fromTo(d, { opacity: 0, y: 0 }, { opacity: 0.25 + r() * 0.6, y: -(40 + r() * 160), x: (r() - 0.5) * 80, duration: dura, ease: "none" }, t);
    }
  };

  /* contador animado (grados, %, km/h…) */
  E.contador = function (tl, sel, t, desde, hasta, dura, sufijo) {
    const el = document.querySelector(sel), o = { v: desde };
    tl.to(o, { v: hasta, duration: dura || 1, ease: "power2.out", onUpdate: function () { el.textContent = Math.round(o.v) + (sufijo || ""); } }, t);
  };

  /* lupa que entra y revela el detalle */
  E.lupa = function (tl, sel, t, dx, dy) {
    tl.fromTo(sel, { x: dx || 300, y: dy || 300, scale: 0.6, opacity: 0, rotation: 12 },
      { x: 0, y: 0, scale: 1, opacity: 1, rotation: 0, duration: 0.6, ease: "power3.out" }, t);
  };

  window.EI = E;
})();
