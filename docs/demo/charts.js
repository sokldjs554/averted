/* 차트 프리미티브 — 의존성 없는 인라인 SVG. dataviz 규칙: 얇은 마크(선 2px, 막대 ≤ 24px·끝만 4px 라운드),
 * 눈금선은 연한 실선, 값 라벨은 선택적으로, 텍스트는 잉크 토큰(시리즈 색을 쓰지 않음), 범례는 시리즈 2개 이상일 때 항상,
 * 모든 값은 툴팁과 "표로 보기"로도 읽힌다. 라벨은 신뢰할 수 없는 데이터이므로 전부 textContent 로 넣는다. */
(function (root) {
  const SVGNS = "http://www.w3.org/2000/svg";
  const el = (tag, attrs = {}, text) => {
    const e = tag.startsWith("svg:") ? document.createElementNS(SVGNS, tag.slice(4)) : document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) if (v !== undefined && v !== null) e.setAttribute(k, v);
    if (text !== undefined) e.textContent = text;
    return e;
  };
  const fmtN = (n, d = 0) => (n == null || Number.isNaN(n) ? "–" : Number(n).toLocaleString("ko-KR", { maximumFractionDigits: d }));
  const fmtP = (p, d = 1) => (p == null || Number.isNaN(p) ? "–" : (p * 100).toFixed(d) + " %");
  /* viewBox 폭을 컨테이너 폭에 맞춰 글자 크기가 화면 폭과 무관하게 거의 일정하게 보이게 한다 */
  const chartWidth = (container) => Math.round(Math.min(760, Math.max(300, container.clientWidth || 680)));

  /* ---------- 툴팁 ---------- */
  let tip;
  function tooltip() {
    if (!tip) { tip = el("div", { class: "tooltip", hidden: "", role: "status" }); document.body.appendChild(tip); }
    return tip;
  }
  function showTip(x, y, title, rows) {
    const t = tooltip();
    t.replaceChildren();
    if (title) t.appendChild(el("div", { class: "t" }, title));
    for (const r of rows) {
      const row = el("div", { class: "row" });
      const left = el("span");
      if (r.color) { const k = el("span", { class: "k" }); k.style.background = r.color; left.appendChild(k); }
      left.appendChild(document.createTextNode(r.label));
      row.appendChild(left);
      row.appendChild(el("b", {}, r.value));
      t.appendChild(row);
    }
    t.hidden = false;
    const w = t.offsetWidth, h = t.offsetHeight;
    t.style.left = Math.max(8, Math.min(x + 14, window.innerWidth - w - 8)) + "px";
    t.style.top = Math.max(8, y - h - 12) + "px";
  }
  const hideTip = () => { if (tip) tip.hidden = true; };

  function niceTicks(a, b, n) {
    const span = b - a || 1, step0 = span / n, mag = Math.pow(10, Math.floor(Math.log10(step0)));
    const step = [1, 2, 2.5, 5, 10].map((c) => c * mag).find((c) => span / c <= n) || 10 * mag;
    const out = [];
    for (let v = Math.ceil(a / step - 1e-9) * step; v <= b + 1e-9; v += step) out.push(+v.toFixed(10));
    return out;
  }

  /* ---------- 표로 보기 ---------- */
  function tableView(container, headers, rows, summary = "표로 보기") {
    const d = el("details", { class: "tableview" });
    d.appendChild(el("summary", {}, summary));
    const t = el("table", { class: "data" });
    const tr = el("tr");
    headers.forEach((h, i) => tr.appendChild(el("th", { class: i ? "num" : "" }, h)));
    t.appendChild(el("thead")).appendChild(tr);
    const tb = el("tbody");
    for (const r of rows) {
      const row = el("tr");
      r.forEach((c, i) => row.appendChild(el("td", { class: i ? "num" : "" }, String(c))));
      tb.appendChild(row);
    }
    t.appendChild(tb);
    d.appendChild(t);
    container.appendChild(d);
  }

  /* ---------- 범례 ---------- */
  function legend(items) {
    const lg = el("div", { class: "legend" });
    for (const it of items) {
      const i = el("span");
      const k = el("span", { class: "key" + (it.rect ? " rect" : "") });
      k.style.background = it.color;
      if (it.thin) k.style.height = "1px";
      i.appendChild(k);
      i.appendChild(document.createTextNode(it.label));
      lg.appendChild(i);
    }
    return lg;
  }

  /* ---------- 선 차트 ----------
   * series: [{name, color, points:[{x:number, y:number|null}], markers?, area?, width?, endLabel?}]
   * opts: {height, y0, y1, fmtX, fmtY, xTicks, refY, label, onPick(x), marker:{x}} */
  function lineChart(container, series, opts = {}) {
    container.replaceChildren();
    const W = chartWidth(container), H = opts.height || 220, m = { l: 48, r: opts.rightPad ?? 16, t: 12, b: 28 };
    const xs = series.flatMap((s) => s.points.map((p) => +p.x));
    const ys = series.flatMap((s) => s.points.map((p) => p.y)).filter((v) => v != null);
    if (!xs.length) { container.appendChild(el("div", { class: "empty" }, "데이터 없음")); return null; }
    const x0 = Math.min(...xs), x1 = Math.max(...xs);
    let y0 = opts.y0 ?? Math.min(0, ...ys), y1 = opts.y1 ?? Math.max(...ys);
    if (y1 === y0) y1 = y0 + 1;
    if (opts.y1 == null) y1 += (y1 - y0) * 0.08;
    const sx = (v) => m.l + ((v - x0) / (x1 - x0 || 1)) * (W - m.l - m.r);
    const sy = (v) => m.t + (1 - (v - y0) / (y1 - y0)) * (H - m.t - m.b);
    const svg = el("svg:svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.label || "" });
    const grid = el("svg:g", { class: "grid" });
    for (const t of niceTicks(y0, y1, 4)) {
      grid.appendChild(el("svg:line", { x1: m.l, x2: W - m.r, y1: sy(t), y2: sy(t) }));
      svg.appendChild(el("svg:text", { x: m.l - 6, y: sy(t) + 3, "text-anchor": "end" }, opts.fmtY ? opts.fmtY(t) : fmtN(t, 2)));
    }
    svg.insertBefore(grid, svg.firstChild);
    const base = sy(Math.max(y0, Math.min(0, y1)));
    svg.appendChild(el("svg:g", { class: "axis" })).appendChild(el("svg:line", { x1: m.l, x2: W - m.r, y1: base, y2: base }));
    const xt = opts.xTicks ?? 5;
    for (let i = 0; i <= xt; i++) {
      const v = x0 + ((x1 - x0) * i) / xt;
      svg.appendChild(el("svg:text", { x: sx(v), y: H - 8, "text-anchor": i === 0 ? "start" : i === xt ? "end" : "middle" }, opts.fmtX ? opts.fmtX(v) : fmtN(v)));
    }
    if (opts.refY != null) svg.appendChild(el("svg:line", { x1: m.l, x2: W - m.r, y1: sy(opts.refY), y2: sy(opts.refY), stroke: "var(--axis)", "stroke-width": 1 }));
    for (const s of series) {
      const pts = s.points.filter((p) => p.y != null);
      if (!pts.length) continue;
      const d = pts.map((p, i) => `${i ? "L" : "M"}${sx(+p.x).toFixed(1)},${sy(p.y).toFixed(1)}`).join("");
      if (s.area) svg.appendChild(el("svg:path", { class: "area", fill: s.color, d: d + `L${sx(+pts[pts.length - 1].x)},${base}L${sx(+pts[0].x)},${base}Z` }));
      svg.appendChild(el("svg:path", { class: "line", stroke: s.color, "stroke-width": s.width || 2, d }));
      if (s.markers) for (const p of pts) svg.appendChild(el("svg:circle", { class: "marker", cx: sx(+p.x), cy: sy(p.y), r: 4, fill: s.color }));
      if (s.endLabel) {
        const last = pts[pts.length - 1];
        svg.appendChild(el("svg:text", { x: sx(+last.x) + 8, y: sy(last.y) + 4, class: "endlabel" }, s.endLabel(last)));
      }
    }
    let pick = null;
    if (opts.marker != null) {
      const mx = sx(opts.marker);
      svg.appendChild(el("svg:line", { x1: mx, x2: mx, y1: m.t, y2: H - m.b, stroke: "var(--text-primary)", "stroke-width": 1, "stroke-opacity": 0.28 }));
    }
    const cross = el("svg:line", { class: "crosshair", y1: m.t, y2: H - m.b, visibility: "hidden" });
    svg.appendChild(cross);
    const hit = el("svg:rect", { class: "hit", x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, tabindex: "0" });
    const nearest = (clientX) => {
      const r = svg.getBoundingClientRect();
      const xv = x0 + (((clientX - r.left) * W) / r.width - m.l) / (W - m.l - m.r) * (x1 - x0);
      let best = null, bd = Infinity;
      for (const p of series[0].points) { const dd = Math.abs(+p.x - xv); if (dd < bd) { bd = dd; best = p; } }
      return best;
    };
    const rowsAt = (x) => series.map((s) => { const q = s.points.find((p) => +p.x === +x); return { label: s.name, color: s.color, value: q && q.y != null ? (opts.fmtY ? opts.fmtY(q.y) : fmtN(q.y, 2)) : "–" }; });
    hit.addEventListener("pointermove", (ev) => {
      const b = nearest(ev.clientX);
      if (!b) return;
      cross.setAttribute("x1", sx(+b.x)); cross.setAttribute("x2", sx(+b.x)); cross.setAttribute("visibility", "visible");
      showTip(ev.clientX, ev.clientY, opts.fmtX ? opts.fmtX(+b.x) : String(b.x), rowsAt(b.x));
    });
    hit.addEventListener("pointerleave", () => { cross.setAttribute("visibility", "hidden"); hideTip(); });
    if (opts.onPick) hit.addEventListener("click", (ev) => { const b = nearest(ev.clientX); if (b) opts.onPick(+b.x); });
    svg.appendChild(hit);
    if (series.length > 1) container.appendChild(legend(series.map((s) => ({ label: s.name, color: s.color, thin: s.width === 1 }))));
    container.appendChild(svg);
    if (opts.table) tableView(container, opts.table.headers, opts.table.rows);
    return pick;
  }

  /* ---------- 가로 막대 ----------
   * rows: [{label, value, color?, sub?, lo?, hi?, note?}] — 음수 허용(발산), lo/hi 가 있으면 신뢰구간 수염 */
  function hbars(container, rows, opts = {}) {
    container.replaceChildren();
    if (!rows.length) { container.appendChild(el("div", { class: "empty" }, "데이터 없음")); return; }
    const W = chartWidth(container), bh = opts.barHeight || 18, gap = opts.gap || 10, labelW = Math.min(opts.labelW || 150, Math.round(W * 0.46)), valueW = opts.valueW || 74, H = rows.length * (bh + gap) + 6;
    const svg = el("svg:svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.label || "" });
    const vals = rows.flatMap((r) => [r.value, r.hi ?? r.value]);
    const neg = Math.min(0, ...rows.map((r) => r.value)), pos = Math.max(opts.max ?? 0, ...vals);
    const x0 = labelW, x1 = W - valueW, sx = (v) => x0 + ((v - neg) / (pos - neg || 1)) * (x1 - x0), zero = sx(0);
    svg.appendChild(el("svg:line", { x1: zero, x2: zero, y1: 0, y2: H, stroke: "var(--axis)" }));
    rows.forEach((r, i) => {
      const y = 3 + i * (bh + gap), w = Math.max(1, Math.abs(sx(r.value) - zero)), rx = 4;
      const color = r.color || (r.value < 0 ? "var(--div-neg)" : opts.diverging ? "var(--div-pos)" : "var(--series-1)");
      const d = r.value >= 0
        ? `M${zero},${y}h${Math.max(0, w - rx)}a${rx},${rx} 0 0 1 ${rx},${rx}v${bh - 2 * rx}a${rx},${rx} 0 0 1 -${rx},${rx}h-${Math.max(0, w - rx)}z`
        : `M${zero},${y}h-${Math.max(0, w - rx)}a${rx},${rx} 0 0 0 -${rx},${rx}v${bh - 2 * rx}a${rx},${rx} 0 0 0 ${rx},${rx}h${Math.max(0, w - rx)}z`;
      const p = el("svg:path", { d, fill: color, class: "bar-mark", tabindex: "0" });
      const tipRows = [{ label: opts.valueName || "값", value: opts.fmt ? opts.fmt(r.value) : fmtN(r.value, 3) }];
      if (r.lo != null) tipRows.push({ label: "95% 신뢰구간", value: `${opts.fmt ? opts.fmt(r.lo) : r.lo} ~ ${opts.fmt ? opts.fmt(r.hi) : r.hi}` });
      if (r.sub) tipRows.push({ label: "", value: r.sub });
      const show = (ev) => { const b = (ev.currentTarget || p).getBoundingClientRect(); showTip(ev.clientX || b.left + b.width / 2, ev.clientY || b.top, r.label, tipRows); };
      p.addEventListener("pointermove", show); p.addEventListener("focus", show);
      p.addEventListener("pointerleave", hideTip); p.addEventListener("blur", hideTip);
      svg.appendChild(p);
      if (r.lo != null && r.hi != null) {
        const cy = y + bh / 2;
        const g = el("svg:g", { stroke: "var(--text-secondary)", "stroke-width": 1.5 });
        g.appendChild(el("svg:line", { x1: sx(r.lo), x2: sx(r.hi), y1: cy, y2: cy }));
        g.appendChild(el("svg:line", { x1: sx(r.lo), x2: sx(r.lo), y1: cy - 4, y2: cy + 4 }));
        g.appendChild(el("svg:line", { x1: sx(r.hi), x2: sx(r.hi), y1: cy - 4, y2: cy + 4 }));
        svg.appendChild(g);
      }
      const maxChars = Math.max(8, Math.floor((labelW - 10) / 7.2)), lab = r.label.length > maxChars ? r.label.slice(0, maxChars - 1) + "…" : r.label;
      svg.appendChild(el("svg:text", { x: labelW - 8, y: y + bh / 2 + 4, "text-anchor": "end", class: "rowlabel" }, lab));
      const tx = (r.hi != null ? sx(r.hi) : r.value >= 0 ? sx(r.value) : sx(r.value)) + (r.value >= 0 ? 8 : -8);
      svg.appendChild(el("svg:text", { x: tx, y: y + bh / 2 + 4, "text-anchor": r.value >= 0 ? "start" : "end", class: "valuelabel" }, opts.fmt ? opts.fmt(r.value) : fmtN(r.value, 3)));
    });
    container.appendChild(svg);
    if (opts.table !== false) tableView(container, ["항목", opts.valueName || "값", ...(rows.some((r) => r.lo != null) ? ["95% 신뢰구간", "n"] : [])],
      rows.map((r) => [r.label, opts.fmt ? opts.fmt(r.value) : fmtN(r.value, 3), ...(r.lo != null ? [`${opts.fmt ? opts.fmt(r.lo) : r.lo} ~ ${opts.fmt ? opts.fmt(r.hi) : r.hi}`, r.note ?? ""] : [])]));
  }

  /* ---------- 표 ---------- */
  function table(container, cols, rows, onRow) {
    container.replaceChildren();
    if (!rows.length) { container.appendChild(el("div", { class: "empty" }, "데이터 없음")); return; }
    const t = el("table", { class: "data" });
    const tr = el("tr");
    for (const c of cols) tr.appendChild(el("th", { class: (c.num ? "num " : "") + (c.nowrap ? "nowrap" : "") }, c.h));
    t.appendChild(el("thead")).appendChild(tr);
    const tb = el("tbody");
    for (const r of rows) {
      const row = el("tr", { class: onRow ? "clickable" : "", tabindex: onRow ? "0" : null });
      for (const c of cols) {
        const td = el("td", { class: (c.num ? "num " : "") + (c.nowrap ? "nowrap" : "") });
        const v = c.render ? c.render(r) : r[c.k];
        if (v instanceof Node) td.appendChild(v); else td.textContent = v == null ? "–" : String(v);
        row.appendChild(td);
      }
      if (onRow) {
        row.addEventListener("click", () => onRow(r));
        row.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onRow(r); } });
      }
      tb.appendChild(row);
    }
    t.appendChild(tb);
    container.appendChild(t);
  }

  /* ---------- 작은 부품 ---------- */
  function pbar(p, max = 0.5, width = 110) {
    const wrap = el("span", { class: "pbar" });
    const tr = el("span", { class: "bar-track" });
    tr.style.width = width + "px";
    const b = el("span", { class: "bar" });
    b.style.width = Math.max(2, Math.min(1, p / max) * width) + "px";
    tr.appendChild(b);
    wrap.appendChild(tr);
    wrap.appendChild(document.createTextNode(fmtP(p)));
    return wrap;
  }
  function badge(kind, text) {
    const b = el("span", { class: `badge ${kind}` });
    b.appendChild(el("span", { class: "dot", "aria-hidden": "true" }));
    b.appendChild(document.createTextNode(text));
    return b;
  }
  function tile(label, value, sub, subCls) {
    const t = el("div", { class: "tile" });
    t.appendChild(el("div", { class: "label" }, label));
    t.appendChild(el("div", { class: "value" }, value));
    if (sub) t.appendChild(el("div", { class: `delta ${subCls || ""}` }, sub));
    return t;
  }

  /* ---------- 모양 범례 (색만으로 구분하지 않는다) ---------- */
  function shapeLegend(items) {
    const lg = el("div", { class: "legend" });
    for (const it of items) {
      const s = el("span");
      const svg = el("svg:svg", { width: 18, height: 14, viewBox: "0 0 18 14", "aria-hidden": "true" });
      if (it.shape === "ring") svg.appendChild(el("svg:circle", { cx: 9, cy: 7, r: 5, fill: "none", stroke: it.color, "stroke-width": 1.8 }));
      else if (it.shape === "dot") svg.appendChild(el("svg:circle", { cx: 9, cy: 7, r: it.r || 3, fill: it.color, opacity: it.opacity ?? 1 }));
      else if (it.shape === "both") { svg.appendChild(el("svg:circle", { cx: 9, cy: 7, r: 5.5, fill: "none", stroke: it.ring, "stroke-width": 1.8 })); svg.appendChild(el("svg:circle", { cx: 9, cy: 7, r: 3, fill: it.color })); }
      else if (it.shape === "diamond") svg.appendChild(el("svg:path", { d: "M9,2L14,7L9,12L4,7Z", fill: "var(--surface-1)", stroke: it.color, "stroke-width": 1.6 }));
      else if (it.shape === "dash") svg.appendChild(el("svg:line", { x1: 2, x2: 16, y1: 7, y2: 7, stroke: it.color, "stroke-width": 1.5, "stroke-dasharray": "3 3" }));
      else if (it.shape === "rect") svg.appendChild(el("svg:rect", { x: 3, y: 3, width: 12, height: 8, rx: 2, fill: it.fill || it.color, stroke: it.stroke || "none", "stroke-width": 1.5 }));
      s.appendChild(svg);
      s.appendChild(document.createTextNode(it.label));
      lg.appendChild(s);
    }
    return lg;
  }

  /* ---------- 신뢰구간 점 차트 ----------
   * rows: [{label, value, lo, hi, color?, sub?}]   opts: {fmt, refs:[{x,label}], label, labelW, zeroLabel} */
  function forest(container, rows, opts = {}) {
    container.replaceChildren();
    if (!rows.length) { container.appendChild(el("div", { class: "empty" }, "데이터 없음")); return; }
    const W = chartWidth(container), rowH = 36, labelW = Math.min(opts.labelW || 150, Math.round(W * 0.36)), m = { l: labelW, r: 64, t: 24, b: 26 };
    const H = m.t + rows.length * rowH + m.b;
    const refs = opts.refs || [];
    const all = rows.flatMap((r) => [r.lo ?? r.value, r.hi ?? r.value, r.value]).concat(refs.map((r) => r.x));
    let a = Math.min(0, ...all), b = Math.max(0, ...all);
    const pad = (b - a) * 0.08 || 1; a -= pad; b += pad;
    const sx = (v) => m.l + ((v - a) / (b - a)) * (W - m.l - m.r);
    const fmt = opts.fmt || ((v) => fmtN(v, 2));
    const svg = el("svg:svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.label || "" });
    const grid = el("svg:g", { class: "grid" });
    for (const t of niceTicks(a, b, 5)) {
      grid.appendChild(el("svg:line", { x1: sx(t), x2: sx(t), y1: m.t, y2: H - m.b }));
      svg.appendChild(el("svg:text", { x: sx(t), y: H - 8, "text-anchor": "middle" }, fmt(t)));
    }
    svg.insertBefore(grid, svg.firstChild);
    svg.appendChild(el("svg:line", { x1: sx(0), x2: sx(0), y1: m.t - 4, y2: H - m.b, stroke: "var(--axis)", "stroke-width": 1.5 }));
    refs.forEach((r, i) => {
      svg.appendChild(el("svg:line", { x1: sx(r.x), x2: sx(r.x), y1: m.t - 4, y2: H - m.b, stroke: "var(--text-primary)", "stroke-width": 1.5, "stroke-dasharray": "4 3" }));
      svg.appendChild(el("svg:text", { x: sx(r.x), y: 12 + (i % 2) * 0, "text-anchor": "middle", class: "rowlabel" }, r.label));
    });
    rows.forEach((r, i) => {
      const cy = m.t + i * rowH + rowH / 2;
      const g = el("svg:g", { class: "bar-mark", tabindex: "0" });
      if (r.lo != null) {
        g.appendChild(el("svg:line", { x1: sx(r.lo), x2: sx(r.hi), y1: cy, y2: cy, stroke: "var(--text-secondary)", "stroke-width": 1.8 }));
        g.appendChild(el("svg:line", { x1: sx(r.lo), x2: sx(r.lo), y1: cy - 5, y2: cy + 5, stroke: "var(--text-secondary)", "stroke-width": 1.8 }));
        g.appendChild(el("svg:line", { x1: sx(r.hi), x2: sx(r.hi), y1: cy - 5, y2: cy + 5, stroke: "var(--text-secondary)", "stroke-width": 1.8 }));
      }
      g.appendChild(el("svg:circle", { cx: sx(r.value), cy, r: 6, fill: r.color || "var(--series-1)", stroke: "var(--surface-1)", "stroke-width": 2 }));
      const rowsTip = [{ label: "추정", value: fmt(r.value) }];
      if (r.lo != null) rowsTip.push({ label: "95% 구간", value: `${fmt(r.lo)} ~ ${fmt(r.hi)}` });
      if (r.sub) rowsTip.push({ label: "", value: r.sub });
      const show = (ev) => { const bb = ev.currentTarget.getBoundingClientRect(); showTip(ev.clientX || bb.left + bb.width / 2, ev.clientY || bb.top, r.label, rowsTip); };
      g.addEventListener("pointermove", show); g.addEventListener("focus", show);
      g.addEventListener("pointerleave", hideTip); g.addEventListener("blur", hideTip);
      svg.appendChild(g);
      const maxChars = Math.max(6, Math.floor((labelW - 10) / 11.5));
      svg.appendChild(el("svg:text", { x: labelW - 10, y: cy + 4, "text-anchor": "end", class: "rowlabel" }, r.label.length > maxChars ? r.label.slice(0, maxChars - 1) + "…" : r.label));
      svg.appendChild(el("svg:text", { x: W - m.r + 8, y: cy + 4, class: "valuelabel" }, fmt(r.value)));
    });
    container.appendChild(svg);
    tableView(container, ["항목", "추정", "95% 구간"], rows.map((r) => [r.label, fmt(r.value), r.lo != null ? `${fmt(r.lo)} ~ ${fmt(r.hi)}` : "–"]));
  }

  /* ---------- 산점도 ----------
   * pts: [{x, y, kind:"none"|"risk"|"effect"|"both", title, rows:[{label,value}]}]   opts: {fmtX, fmtY, xlabel, ylabel, height} */
  function scatter(container, pts, opts = {}) {
    container.replaceChildren();
    if (!pts.length) { container.appendChild(el("div", { class: "empty" }, "데이터 없음")); return; }
    const W = chartWidth(container), H = opts.height || 300, m = { l: 54, r: 14, t: 14, b: 40 };
    const xs = pts.map((p) => p.x), ys = pts.map((p) => p.y);
    const x0 = 0, x1 = Math.max(...xs) * 1.04;
    let y0 = Math.min(0, ...ys), y1 = Math.max(...ys);
    const ypad = (y1 - y0) * 0.08 || 0.01; y0 -= y0 < 0 ? ypad : 0; y1 += ypad;
    const sx = (v) => m.l + ((v - x0) / (x1 - x0 || 1)) * (W - m.l - m.r);
    const sy = (v) => m.t + (1 - (v - y0) / (y1 - y0 || 1)) * (H - m.t - m.b);
    const svg = el("svg:svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.label || "" });
    const grid = el("svg:g", { class: "grid" });
    for (const t of niceTicks(y0, y1, 5)) {
      grid.appendChild(el("svg:line", { x1: m.l, x2: W - m.r, y1: sy(t), y2: sy(t) }));
      svg.appendChild(el("svg:text", { x: m.l - 6, y: sy(t) + 3, "text-anchor": "end" }, opts.fmtY ? opts.fmtY(t) : fmtN(t, 3)));
    }
    for (const t of niceTicks(x0, x1, 5)) {
      grid.appendChild(el("svg:line", { x1: sx(t), x2: sx(t), y1: m.t, y2: H - m.b }));
      svg.appendChild(el("svg:text", { x: sx(t), y: H - m.b + 14, "text-anchor": "middle" }, opts.fmtX ? opts.fmtX(t) : fmtN(t, 2)));
    }
    svg.insertBefore(grid, svg.firstChild);
    svg.appendChild(el("svg:line", { x1: m.l, x2: W - m.r, y1: sy(0), y2: sy(0), stroke: "var(--axis)", "stroke-width": 1.5 }));
    svg.appendChild(el("svg:text", { x: (m.l + W - m.r) / 2, y: H - 6, "text-anchor": "middle", class: "rowlabel" }, opts.xlabel || ""));
    svg.appendChild(el("svg:text", { x: m.l, y: 9, "text-anchor": "start", class: "rowlabel" }, opts.ylabel || ""));
    const order = { none: 0, risk: 1, effect: 2, both: 3 };
    [...pts].sort((p, q) => order[p.kind] - order[q.kind]).forEach((p) => {
      const cx = sx(p.x), cy = sy(p.y);
      let node;
      if (p.kind === "none") node = el("svg:circle", { cx, cy, r: 2.6, fill: "var(--deemph)", opacity: 0.75 });
      else if (p.kind === "risk") node = el("svg:circle", { cx, cy, r: 5.5, fill: "none", stroke: "var(--series-2)", "stroke-width": 1.8 });
      else if (p.kind === "effect") node = el("svg:circle", { cx, cy, r: 5, fill: "var(--series-1)", stroke: "var(--surface-1)", "stroke-width": 1.5 });
      else { node = el("svg:g"); node.appendChild(el("svg:circle", { cx, cy, r: 7, fill: "none", stroke: "var(--series-2)", "stroke-width": 1.8 })); node.appendChild(el("svg:circle", { cx, cy, r: 4, fill: "var(--series-1)" })); }
      if (p.kind !== "none" || pts.length < 400) {
        const show = (ev) => showTip(ev.clientX, ev.clientY, p.title, p.rows || []);
        node.addEventListener("pointermove", show); node.addEventListener("pointerleave", hideTip);
      }
      svg.appendChild(node);
    });
    container.appendChild(shapeLegend([
      { shape: "dot", color: "var(--deemph)", label: "전체 설비" },
      { shape: "ring", color: "var(--series-2)", label: "위험순이 고른 설비" },
      { shape: "dot", color: "var(--series-1)", r: 4, label: "효과순이 고른 설비" },
      { shape: "both", color: "var(--series-1)", ring: "var(--series-2)", label: "둘 다" },
    ]));
    container.appendChild(svg);
    const sel = pts.filter((p) => p.kind !== "none").sort((p, q) => q.y - p.y).slice(0, 40);
    tableView(container, opts.tableHeaders || ["설비", "x", "y", "선택"], sel.map((p) => [p.title, opts.fmtX ? opts.fmtX(p.x) : p.x, opts.fmtY ? opts.fmtY(p.y) : p.y, { risk: "위험순", effect: "효과순", both: "둘 다" }[p.kind]]), "선택된 설비 표로 보기");
  }

  /* ---------- 정책 비교 막대 ----------
   * rows: [{label, value, lo?, hi?, ope?, opeLo?, opeHi?, tone:"ours"|"risk"|"other"|"base"|"ref", sub?}]
   * 막대 = 정답 기준(시뮬레이터가 아는 효과의 합), ◇ = 로그만으로 추정한 값(OPE) */
  function policyBars(container, rows, opts = {}) {
    container.replaceChildren();
    const W = chartWidth(container), labelW = Math.min(opts.labelW || 220, Math.round(W * 0.42)), valueW = 56, bh = 14, rowH = 40;
    const H = rows.length * rowH + 28;
    const vals = rows.flatMap((r) => [r.value, r.hi ?? r.value, r.ope ?? 0, r.opeHi ?? 0]);
    const max = Math.max(...vals) * 1.04, min = Math.min(0, ...rows.map((r) => Math.min(r.opeLo ?? 0, r.ope ?? 0, r.value)));
    const x0 = labelW, x1 = W - valueW, sx = (v) => x0 + ((v - min) / (max - min || 1)) * (x1 - x0), zero = sx(0);
    const svg = el("svg:svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.label || "" });
    const grid = el("svg:g", { class: "grid" });
    for (const t of niceTicks(min, max, 5)) {
      grid.appendChild(el("svg:line", { x1: sx(t), x2: sx(t), y1: 0, y2: H - 22 }));
      svg.appendChild(el("svg:text", { x: sx(t), y: H - 6, "text-anchor": "middle" }, fmtN(t, 1)));
    }
    svg.insertBefore(grid, svg.firstChild);
    svg.appendChild(el("svg:line", { x1: zero, x2: zero, y1: 0, y2: H - 22, stroke: "var(--axis)", "stroke-width": 1.5 }));
    const fill = { ours: "var(--series-1)", risk: "var(--series-2)", other: "color-mix(in srgb, var(--series-1) 38%, var(--surface-1))", base: "var(--deemph)" };
    rows.forEach((r, i) => {
      const y = 4 + i * rowH, w = Math.max(1, sx(Math.max(r.value, 0)) - zero), rx = 4;
      let node;
      if (r.tone === "ref") node = el("svg:rect", { x: zero, y, width: w, height: bh, rx, fill: "none", stroke: "var(--text-secondary)", "stroke-width": 1.5, "stroke-dasharray": "4 3" });
      else node = el("svg:path", { d: `M${zero},${y}h${Math.max(0, w - rx)}a${rx},${rx} 0 0 1 ${rx},${rx}v${bh - 2 * rx}a${rx},${rx} 0 0 1 -${rx},${rx}h-${Math.max(0, w - rx)}z`, fill: fill[r.tone] || fill.other });
      node.setAttribute("class", "bar-mark"); node.setAttribute("tabindex", "0");
      const tip = [{ label: "정답 기준", value: fmtN(r.value, 2) }];
      if (r.lo != null) tip.push({ label: "95% 구간", value: `${fmtN(r.lo, 2)} ~ ${fmtN(r.hi, 2)}` });
      if (r.ope != null) tip.push({ label: "로그만으로 추정(OPE)", value: fmtN(r.ope, 2) + (r.opeLo != null ? `  (${fmtN(r.opeLo, 1)} ~ ${fmtN(r.opeHi, 1)})` : "") });
      if (r.sub) tip.push({ label: "", value: r.sub });
      const show = (ev) => { const bb = ev.currentTarget.getBoundingClientRect(); showTip(ev.clientX || bb.left + bb.width / 2, ev.clientY || bb.top, r.label, tip); };
      node.addEventListener("pointermove", show); node.addEventListener("focus", show);
      node.addEventListener("pointerleave", hideTip); node.addEventListener("blur", hideTip);
      svg.appendChild(node);
      if (r.lo != null) {
        const cy = y + bh / 2, g = el("svg:g", { stroke: "var(--text-primary)", "stroke-width": 1.4 });
        g.appendChild(el("svg:line", { x1: sx(r.lo), x2: sx(r.hi), y1: cy, y2: cy }));
        g.appendChild(el("svg:line", { x1: sx(r.hi), x2: sx(r.hi), y1: cy - 3, y2: cy + 3 }));
        svg.appendChild(g);
      }
      if (r.ope != null) {
        const cy = y + bh + 11;
        if (r.opeLo != null) svg.appendChild(el("svg:line", { x1: sx(r.opeLo), x2: sx(r.opeHi), y1: cy, y2: cy, stroke: "var(--muted)", "stroke-width": 1.4, "stroke-dasharray": "3 3" }));
        const cx = sx(r.ope);
        svg.appendChild(el("svg:path", { d: `M${cx},${cy - 5}L${cx + 5},${cy}L${cx},${cy + 5}L${cx - 5},${cy}Z`, fill: "var(--surface-1)", stroke: "var(--text-primary)", "stroke-width": 1.6 }));
      }
      const maxChars = Math.max(6, Math.floor((labelW - 10) / 11.5));
      svg.appendChild(el("svg:text", { x: labelW - 10, y: y + bh / 2 + 4, "text-anchor": "end", class: "rowlabel" }, r.label.length > maxChars ? r.label.slice(0, maxChars - 1) + "…" : r.label));
      svg.appendChild(el("svg:text", { x: sx(r.hi ?? r.value) + 8, y: y + bh / 2 + 4, class: "valuelabel" }, r.value.toFixed(2)));
    });
    container.appendChild(shapeLegend([
      { shape: "rect", color: "var(--series-1)", label: "점검 100번당 막는 고장 — 정답 기준" },
      ...(rows.some((r) => r.ope != null) ? [{ shape: "diamond", color: "var(--text-primary)", label: "로그만으로 추정한 값(OPE)" }] : []),
    ]));
    container.appendChild(svg);
    tableView(container, ["정책", "정답 기준", "95% 구간", "OPE", "OPE 구간"], rows.map((r) => [r.label, r.value.toFixed(2), r.lo != null ? `${fmtN(r.lo, 2)} ~ ${fmtN(r.hi, 2)}` : "–", r.ope != null ? fmtN(r.ope, 2) : "–", r.opeLo != null ? `${fmtN(r.opeLo, 1)} ~ ${fmtN(r.opeHi, 1)}` : "–"]));
  }

  function verdictBadge(level) {
    const map = { green: ["good", "확인 가능한 문제 없음"], yellow: ["legal", "주의"], red: ["fail", "신뢰 불가 신호"] };
    const [cls, text] = map[level] || ["quiet", level];
    return badge(cls, text);
  }


  root.AvertedCharts = { el, fmtN, fmtP, showTip, hideTip, lineChart, hbars, table, tableView, legend, pbar, badge, tile, niceTicks, forest, scatter, policyBars, shapeLegend, verdictBadge };
})(typeof self !== "undefined" ? self : this);
