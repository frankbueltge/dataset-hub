"""Stufe 2 des Relevanzkriteriums: das Kernbestand-Merkmal (Neufassung §4).

Der Kernbestand trägt die Themen der Ökologie. Nur er bekommt Unterseiten und
Sichtbarkeit auf der Website; alles übrige bleibt im Snapshot abfragbar.

**Dreiwertig, nicht zweiwertig.** Ein Stichwortsieb allein wäre entweder zu eng
(verpasst) oder zu weit (schleppt Rauschen ein). Deshalb:

    "regel"     — trifft einen Begriff, der für sich schon entscheidet
    "grenzfall" — trifft nur einen weiten Begriff; die Urteilsroutine entscheidet
    None        — kein Treffer, nicht im Kernbestand

Ein Urteil aus `journal/entscheidungen.jsonl` (`typ: kernbestand` /
`kein_kernbestand`) überstimmt den Sieb immer — der Sieb schlägt vor, das Urteil
entscheidet. Damit wird derselbe Grenzfall nicht monatlich neu gestellt.

Nur Standardbibliothek. Kein Modellaufruf (Bauregel) — das Urteil kommt als
Journal-Ereignis von außen herein.
"""
import re

# ---------------------------------------------------------------------------
# Begriffe, die für sich entscheiden. Bewusst eng gehalten: ein Treffer hier
# nimmt einen Eintrag ohne weitere Prüfung in den Kernbestand auf.
# ---------------------------------------------------------------------------
SICHERE_BEGRIFFE = {
    # Gegenstand: KI-Systeme, ihre Trainingsdaten und ihre Bewertung
    "ki_systeme": [
        r"training data", r"trainingsdaten", r"training (corpus|dataset|set)",
        r"language model", r"sprachmodell", r"large language model", r"\bllm\b",
        r"machine learning (dataset|benchmark|corpus)", r"neural network",
        r"artificial intelligence", r"künstliche intelligenz",
        r"model (card|evaluation|benchmark)", r"\bbenchmark (dataset|suite)\b",
        r"fine-?tuning (data|dataset)", r"instruction (tuning|dataset)",
        r"algorithmic (bias|fairness|accountability|audit)",
        r"algorithmische[nrs]? (verzerrung|diskriminierung)",
    ],
    # Gegenstand: Macht — Verwaltung, Vergabe, Lobbyismus
    "macht_verwaltung": [
        r"public procurement", r"öffentliche vergabe", r"vergabedaten",
        r"tender (data|notices)", r"contract award", r"beneficial ownership",
        r"lobby(ing)? register", r"lobbyregister", r"transparenzregister",
        r"campaign finance", r"parteispenden", r"party donations",
        r"government spending", r"haushaltsdaten", r"budget execution",
        r"subsid(y|ies) register", r"subventionen", r"state aid",
        r"freedom of information", r"informationsfreiheit",
        r"conflict of interest (register|declaration)",
    ],
    # Gegenstand: Überwachung
    "ueberwachung": [
        r"surveillance", r"überwachung", r"facial recognition",
        r"gesichtserkennung", r"biometric (data|identification)",
        r"predictive policing", r"police (stops|misconduct|violence)",
        r"polizeiliche kontrollen", r"censorship", r"zensur",
        r"internet shutdown", r"data retention", r"vorratsdatenspeicherung",
    ],
    # Gegenstand: Militär und Konflikt
    "militaer": [
        r"arms (trade|transfers|exports)", r"rüstungsexport",
        r"military expenditure", r"militärausgaben", r"defen[cs]e spending",
        r"armed conflict", r"conflict events", r"battle deaths",
        r"drone strikes", r"landmine", r"nuclear (warhead|test)",
    ],
    # Gegenstand: Klimapolitik (die Politik, nicht die Messreihe)
    "klimapolitik": [
        r"emission(s)? (inventory|trading|registry)", r"emissionshandel",
        r"carbon (pricing|tax|credits|offset)", r"co2-?bepreisung",
        r"climate (policy|finance|pledges|commitments)", r"klimapolitik",
        r"fossil fuel subsid", r"energiewende", r"just transition",
    ],
    # Gegenstand: amtliche Statistik
    "amtliche_statistik": [
        r"\bcensus\b", r"volkszählung", r"zensus \d{4}",
        r"labour force survey", r"mikrozensus",
        r"national accounts", r"volkswirtschaftliche gesamtrechnung",
        r"consumer price index", r"verbraucherpreisindex",
        r"official statistics", r"amtliche statistik",
    ],
}

# ---------------------------------------------------------------------------
# Weite Begriffe: legen Relevanz nahe, entscheiden sie aber nicht. Ein Treffer
# hier macht den Eintrag zum Grenzfall für die Urteilsroutine.
#
# Der ganze Themenkreis „Datensätze, die selbst eine umstrittene Messung sind"
# (§4) steht hier und NUR hier: ob ein Index, ein Ranking oder ein Score eine
# umstrittene Messung ist, lässt sich nicht an einem Wort erkennen. Genau dafür
# gibt es die zweite Instanz.
# ---------------------------------------------------------------------------
WEITE_BEGRIFFE = [
    r"\bindex\b", r"\branking\b", r"\bscore\b", r"\bindicator", r"\bscoreboard\b",
    r"\brating\b", r"\bcomposite (index|indicator)\b",
    r"inequality", r"ungleichheit", r"poverty", r"armut",
    r"discrimination", r"diskriminierung", r"\bbias\b",
    r"governance", r"corruption", r"korruption", r"accountability",
    r"human rights", r"menschenrechte", r"migration", r"asylum", r"asyl",
    r"surveil", r"privacy", r"datenschutz",
    r"open government", r"transparency", r"transparenz",
    r"electoral", r"\belection", r"wahlergebnis",
    r"social media", r"platform (data|governance)", r"content moderation",
    r"disinformation", r"desinformation", r"misinformation",
]

# Herausgeber, deren Veröffentlichungen als amtliche Statistik gelten. Als Muster,
# nicht als Namensliste: die Zahl statistischer Ämter weltweit ist zu groß, um sie
# zu pflegen, und ihre Namen folgen erkennbaren Formen.
AMTLICHE_HERAUSGEBER = [
    r"statisti(k|sche|cs|cal)", r"\bdestatis\b", r"eurostat", r"\boecd\b",
    r"world bank", r"weltbank", r"united nations", r"vereinte nationen",
    r"census bureau", r"\binsee\b", r"\bistat\b",
    r"office for national statistics", r"bundesamt", r"bundesagentur",
    r"european commission", r"europäische kommission",
]

# ---------------------------------------------------------------------------
# Gegenbegriffe: derselbe Begriff, anderer Gegenstand. Trifft einer davon, wird
# ein sicherer Treffer auf „Grenzfall" ZURÜCKGESTUFT — nicht verworfen. Das
# Register entscheidet solche Fälle nicht im Vorbeigehen, es legt sie vor.
#
# Alle Einträge hier stammen aus dem Sieb-Durchlauf über den Bestand vom 27.07.,
# nicht aus Vermutung: „surveillance" traf die Notaufnahme- und
# Vogelgrippe-Überwachung, „census" eine Handschriften-Zählung.
# ---------------------------------------------------------------------------
GEGENBEGRIFFE = {
    "ueberwachung": [
        # epidemiologische Überwachung — dasselbe Wort, staatsferner Gegenstand
        r"influenza", r"\bvirus", r"pathogen", r"epidemiolog", r"outbreak",
        r"notaufnahme", r"syndromic", r"wastewater", r"sentinel",
        r"disease", r"seuchen", r"avian", r"vector-borne", r"antimicrobial",
    ],
    "amtliche_statistik": [
        # „census" im naturwissenschaftlichen und philologischen Sinn
        r"manuscript", r"handschrift", r"\bgenome", r"\bspecies\b",
        r"forest", r"\btree census", r"vegetation", r"\bstellar\b", r"galax",
        r"coverage census",
    ],
}

_SICHER = {feld: [re.compile(m, re.IGNORECASE) for m in muster]
           for feld, muster in SICHERE_BEGRIFFE.items()}
_GEGEN = {feld: [re.compile(m, re.IGNORECASE) for m in muster]
          for feld, muster in GEGENBEGRIFFE.items()}
_WEIT = [re.compile(m, re.IGNORECASE) for m in WEITE_BEGRIFFE]
_AMTLICH = [re.compile(m, re.IGNORECASE) for m in AMTLICHE_HERAUSGEBER]


def siebe(eintrag: dict):
    """Deterministische Vorsiebung. Rückgabe: (stufe, treffer).

    stufe ist "regel", "grenzfall" oder None; treffer nennt, WORAN es lag —
    ohne diese Angabe wäre das Merkmal eine Behauptung ohne Beleg.

    **Titel und Beschreibung wiegen verschieden**, und das ist der Kern der
    Präzision: Ein sicherer Begriff im TITEL entscheidet, derselbe Begriff nur in
    der BESCHREIBUNG macht bloß einen Grenzfall. Gemessen am Bestand vom 27.07.
    war das der häufigste Fehlgriff — „surveillance" traf die Überwachung von
    Vogelgrippeviren, „language model" einen Verkehrsunfall-Datensatz, der ein
    Sprachmodell nur als verwendetes Werkzeug erwähnt. Der Titel sagt, was ein
    Datensatz IST; die Beschreibung sagt, was er berührt.
    """
    titel = eintrag.get("titel") or ""
    beschreibung = eintrag.get("beschreibung") or ""

    treffer_titel, treffer_beschreibung = [], []
    for feld, muster in _SICHER.items():
        for m in muster:
            fund = m.search(titel)
            if fund:
                treffer_titel.append({"art": "begriff", "feld": feld,
                                      "fund": fund.group(0), "in": "titel"})
                break
            fund = m.search(beschreibung)
            if fund:
                treffer_beschreibung.append({"art": "begriff", "feld": feld,
                                             "fund": fund.group(0), "in": "beschreibung"})
                break
    if treffer_titel:
        # Gegenbegriff im ganzen Text prüfen: der Gegenstand verrät sich oft erst
        # in der Beschreibung („surveillance" im Titel, „influenza" im Fließtext).
        ganzer_text = f"{titel}\n{beschreibung}"
        for t in treffer_titel:
            for m in _GEGEN.get(t["feld"], []):
                fund = m.search(ganzer_text)
                if fund:
                    t["gegenbegriff"] = fund.group(0)
                    break
        if all("gegenbegriff" in t for t in treffer_titel):
            return "grenzfall", treffer_titel
        return "regel", [t for t in treffer_titel if "gegenbegriff" not in t]
    if treffer_beschreibung:
        return "grenzfall", treffer_beschreibung

    herausgeber = eintrag.get("herausgeber") or ""
    for m in _AMTLICH:
        fund = m.search(herausgeber)
        if fund:
            # Ein statistisches Amt allein macht noch keinen Kernbestand — es
            # veröffentlicht auch Geodaten und Verwaltungsinterna. Deshalb
            # Grenzfall, nicht Regel.
            return "grenzfall", [{"art": "herausgeber", "feld": "amtliche_statistik",
                                  "fund": fund.group(0)}]

    for m in _WEIT:
        fund = m.search(f"{titel}\n{beschreibung}")
        if fund:
            return "grenzfall", [{"art": "weiter_begriff", "feld": "offen",
                                  "fund": fund.group(0)}]
    return None, []


def urteile_aus_journal(journal) -> dict:
    """Journal-Ereignisse zum Kernbestand → {eintrag_id: True/False}.

    Späteres Ereignis überstimmt ein früheres (dieselbe Revert-Logik wie bei den
    Merge-Urteilen: ein falsches Urteil wird durch ein neues zurückgenommen).
    """
    urteile = {}
    for ereignis in journal:
        typ = ereignis.get("typ")
        if typ not in ("kernbestand", "kein_kernbestand"):
            continue
        for eid in ereignis.get("mitglieder") or []:
            urteile[eid] = (typ == "kernbestand")
    return urteile


def bestimme(eintrag: dict, urteile: dict):
    """Endgültiges Merkmal eines Eintrags. Rückgabe: (im_kernbestand, herkunft, treffer).

    herkunft ist "urteil", "regel", "grenzfall" oder "kein-treffer" — die Oberfläche
    soll sagen können, WARUM ein Eintrag eine Seite hat.
    """
    stufe, treffer = siebe(eintrag)
    urteil = urteile.get(eintrag.get("id"))
    if urteil is not None:
        return urteil, "urteil", treffer
    if stufe == "regel":
        return True, "regel", treffer
    if stufe == "grenzfall":
        # Unbeurteilte Grenzfälle sind NICHT im Kernbestand. Die Website behauptet
        # damit nie eine Relevanz, die niemand geprüft hat — sie wartet aufs Urteil.
        return False, "grenzfall", treffer
    return False, "kein-treffer", treffer
