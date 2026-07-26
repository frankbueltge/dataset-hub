/* Dataset-Hub — Oberfläche.
 * Zeigt, was aufgenommen wurde: mit Prüfstand, Lücken und leeren Feldern als
 * leeren Feldern. Erfindet nichts und ergänzt nichts, was die Quelle nicht sagt.
 * Rein statisch: liest dieselben Daten, die auch der Snapshot enthält. */

const SEITE = 50;
const $ = (id) => document.getElementById(id);
const zahl = (n) => (n ?? 0).toLocaleString('de-DE');
const escape = (s) => String(s ?? '').replace(/[&<>"']/g,
  (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

let alle = [];
let meta = null;
let fassungsWerke = new Set();
let gefiltert = [];
let gezeigt = 0;

const zustand = { q: '', geprueft: '', lizenz: '', jahr: '', gran: '', nurFassungen: false };

/* ---------- Laden ---------- */

async function laden() {
  try {
    const [e, m] = await Promise.all([
      fetch('daten/eintraege.json').then((r) => {
        if (!r.ok) throw new Error(`eintraege.json: HTTP ${r.status}`);
        return r.json();
      }),
      fetch('daten/meta.json').then((r) => {
        if (!r.ok) throw new Error(`meta.json: HTTP ${r.status}`);
        return r.json();
      }),
    ]);
    alle = e;
    meta = m;
  } catch (fehler) {
    // Ausfall vermerken, nie überbrücken: ein Ladefehler darf nie wie ein leerer
    // Bestand aussehen.
    $('trefferzeile').textContent =
      `Daten konnten nicht geladen werden (${fehler.message}). Das ist ein Ladefehler, ` +
      `kein leerer Bestand.`;
    return;
  }

  const werkZaehler = new Map();
  for (const r of alle) werkZaehler.set(r.w, (werkZaehler.get(r.w) || 0) + 1);
  fassungsWerke = new Set([...werkZaehler].filter(([, n]) => n > 1).map(([w]) => w));

  for (const r of alle) r._s = (r.t + ' ' + r.h).toLowerCase();

  kopfFuellen();
  filterFuellen();
  bestandFuellen();
  verdrahten();
  anwenden();
}

function kopfFuellen() {
  const z = meta.zaehler;
  const felder = [
    ['Einträge', z.eintraege],
    ['Werke', z.werke],
    ['Zugriff bestätigt', z.aufgeloest_bestaetigt],
    ['davon geprüft', z.aufgeloest_versucht],
    ['verworfen', z.abgelehnt_gesamt],
  ];
  $('zaehler').innerHTML = felder
    .map(([k, v]) => `<div><dt>${k}</dt><dd>${zahl(v)}</dd></div>`)
    .join('');
  $('stand').textContent =
    `Schema ${meta.schema_version} · Bestand gebaut ${meta.gebaut_am} · ` +
    `Oberfläche erzeugt ${meta.erzeugt}`;
}

function filterFuellen() {
  const werte = (auswahl) => [...new Set(alle.map(auswahl).filter(Boolean))];

  const lizenzen = werte((r) => r.l).sort();
  $('f-lizenz').insertAdjacentHTML('beforeend',
    `<option value="__leer">(keine Angabe)</option>` +
    lizenzen.map((l) => `<option value="${escape(l)}">${escape(l)}</option>`).join(''));

  const jahre = werte((r) => r.j).sort((a, b) => b - a);
  $('f-jahr').insertAdjacentHTML('beforeend',
    jahre.map((j) => `<option value="${j}">${j}</option>`).join(''));

  const gran = werte((r) => r.g).sort();
  $('f-gran').insertAdjacentHTML('beforeend',
    gran.map((g) => `<option value="${escape(g)}">${escape(g)}</option>`).join(''));
}

/* ---------- Filtern ---------- */

function anwenden() {
  const q = zustand.q.trim().toLowerCase();
  const worte = q ? q.split(/\s+/) : [];

  gefiltert = alle.filter((r) => {
    if (worte.length && !worte.every((w) => r._s.includes(w))) return false;
    if (zustand.geprueft && r.v !== zustand.geprueft) return false;
    if (zustand.lizenz === '__leer') {
      if (r.l) return false;
    } else if (zustand.lizenz && r.l !== zustand.lizenz) return false;
    if (zustand.jahr && !(r.j >= Number(zustand.jahr))) return false;
    if (zustand.gran && r.g !== zustand.gran) return false;
    if (zustand.nurFassungen && !fassungsWerke.has(r.w)) return false;
    return true;
  });

  gezeigt = 0;
  $('ergebnisse').innerHTML = '';
  const t = gefiltert.length;
  $('trefferzeile').textContent = t === alle.length
    ? `${zahl(t)} Einträge`
    : `${zahl(t)} von ${zahl(alle.length)} Einträgen`;

  if (t === 0) {
    // Kein Treffer heißt: im aufgenommenen Bestand nichts gefunden — nicht,
    // dass es das nicht gibt. Der Bestand ist lückenhaft und sagt das auch.
    $('ergebnisse').innerHTML =
      `<li class="treffer leer"><strong>Kein Treffer in diesem Bestand.</strong>
       Das heißt nicht, dass es solche Datensätze nicht gibt — der Hub erntet erst
       seit dem ${escape((meta.quellfenster?.[0]?.seit || '').slice(0, 10))} und
       enthält bisher ${zahl(alle.length)} Einträge.</li>`;
    $('mehr').hidden = true;
    return;
  }
  nachladen();
}

function nachladen() {
  const teil = gefiltert.slice(gezeigt, gezeigt + SEITE);
  $('ergebnisse').insertAdjacentHTML('beforeend', teil.map(karte).join(''));
  gezeigt += teil.length;
  $('mehr').hidden = gezeigt >= gefiltert.length;
  if (!$('mehr').hidden) {
    $('mehr').textContent =
      `weitere ${zahl(Math.min(SEITE, gefiltert.length - gezeigt))} anzeigen ` +
      `(${zahl(gefiltert.length - gezeigt)} übrig)`;
  }
}

/* ---------- Darstellung ---------- */

function pruefMarke(r) {
  if (r.v === 'landing' || r.v === 'download') {
    return `<span class="marke bestaetigt" title="Zugriffsweg per HTTP aufgelöst, ${r.s}">
      Zugriff bestätigt</span>`;
  }
  if (r.v === 'versucht') {
    return `<span class="marke versucht" title="Aufgelöst, aber der Host antwortete mit ${r.s} — ein 403 ist meist Bot-Schutz, kein toter Link">
      geprüft, nicht bestätigt (${r.s ?? '—'})</span>`;
  }
  return `<span class="marke ungeprueft" title="Zugriffsweg wurde noch nicht aufgelöst">
    Zugriff ungeprüft</span>`;
}

function karte(r) {
  const marken = [
    pruefMarke(r),
    r.z === 'ungeprueft'
      ? `<span class="marke ungeprueft" title="Automatisch aufgenommen, inhaltlich nicht gesichtet">Eintrag ungeprüft</span>`
      : '',
    r.l
      ? `<span class="marke lizenz">${escape(r.l)}</span>`
      : `<span class="marke lizenz leer-vermerk" title="Die Quelle nennt keine Lizenz">Lizenz: keine Angabe</span>`,
    fassungsWerke.has(r.w)
      ? `<span class="marke fassungen" title="Dieses Werk hat mehrere Fassungen im Bestand">mehrere Fassungen</span>`
      : '',
  ].filter(Boolean).join('');

  const meta = [
    r.h ? escape(r.h) : `<span class="leer-vermerk">Herausgeber: keine Angabe</span>`,
    r.j ? escape(r.j) : `<span class="leer-vermerk">Jahr: keine Angabe</span>`,
    r.g ? escape(r.g) : '',
    escape(r.q),
  ].filter(Boolean).join('</span><span>');

  return `<li class="treffer">
    <h3><a href="${escape(r.u)}" rel="noopener noreferrer" target="_blank">${escape(r.t)}</a></h3>
    <div class="zeile-meta"><span>${meta}</span></div>
    <div class="zeile-meta"><span class="pid">${escape(r.p)}</span></div>
    <div class="marken">${marken}</div>
  </li>`;
}

function bestandFuellen() {
  const z = meta.zaehler;
  $('luecke').innerHTML =
    `<strong>Bestandslücke, ausgewiesen:</strong> Der Hub erntet ab Aufsetzzeitpunkt ` +
    `vorwärts. Was hier steht, ist das bisher Geerntete — nicht der Weltbestand. ` +
    `Von ${zahl(z.eintraege)} Einträgen sind ${zahl(z.aufgeloest_versucht)} Zugriffswege ` +
    `geprüft, davon ${zahl(z.aufgeloest_bestaetigt)} bestätigt. Der Rest trägt sichtbar ` +
    `„ungeprüft“ — nicht „in Ordnung“.`;

  $('quellfenster').innerHTML = (meta.quellfenster || []).map((f) =>
    `<p><strong>${escape(f.quelle)}</strong><br>
     ${escape(f.seit)} – ${escape(f.bis)}<br>
     ${zahl(f.records)} Fundstellen ·
     ${f.vollstaendig ? 'Lauf vollständig' : '<strong>Lauf unvollständig</strong>'}</p>`
  ).join('') || '<p class="leise">keine Erntemanifeste</p>';

  $('ablehnungen').innerHTML = (meta.ablehnungen || []).length
    ? meta.ablehnungen.map((a) =>
        `<div class="kv"><span>${escape(a.grund)}</span><span>${zahl(a.n)}</span></div>`).join('')
    : '<p class="leise">bisher nichts verworfen</p>';

  $('ausfaelle').innerHTML = (meta.ausfaelle || []).length
    ? meta.ausfaelle.slice(0, 6).map((a) =>
        `<p><strong>${escape(a.quelle)}</strong> ${escape(a.datum)}<br>${escape(a.fehler)}</p>`).join('')
    : '<p class="leise">keine Ausfälle verzeichnet</p>';
}

/* ---------- Verdrahtung ---------- */

function verdrahten() {
  let timer;
  $('suche').addEventListener('input', (e) => {
    clearTimeout(timer);
    timer = setTimeout(() => { zustand.q = e.target.value; anwenden(); }, 120);
  });
  const bind = (id, schluessel, wert = (e) => e.target.value) =>
    $(id).addEventListener('change', (e) => { zustand[schluessel] = wert(e); anwenden(); });
  bind('f-geprueft', 'geprueft');
  bind('f-lizenz', 'lizenz');
  bind('f-jahr', 'jahr');
  bind('f-gran', 'gran');
  bind('f-fassungen', 'nurFassungen', (e) => e.target.checked);
  $('mehr').addEventListener('click', nachladen);
  $('zuruecksetzen').addEventListener('click', () => {
    Object.assign(zustand, { q: '', geprueft: '', lizenz: '', jahr: '', gran: '', nurFassungen: false });
    $('suche').value = '';
    for (const id of ['f-geprueft', 'f-lizenz', 'f-jahr', 'f-gran']) $(id).value = '';
    $('f-fassungen').checked = false;
    anwenden();
  });
}

laden();
