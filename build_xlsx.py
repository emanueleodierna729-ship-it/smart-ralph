#!/usr/bin/env python3
"""Genera saldatrici-usate-buyer.xlsx senza dipendenze esterne (zip + XML)."""
import zipfile, datetime

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))

# ---- Dati ricerca (giugno 2026) ----
HEADERS = ["Azienda", "Paese", "Zona", "Telefono", "Email", "Sito",
           "Tipo", "Cosa compra", "Pagamento", "Ritiro / Logistica",
           "Offerta / prezzo indicativo", "Feedback / recensioni reali",
           "Adatto a lotti 3-5 MIG 300A?", "Fattibilita per il tuo modello"]

ROWS = [
    ["Westermans International", "Regno Unito", "Groby, Leicester", "+44 116 269 6941",
     "welding@westermans.com", "westermans.com", "Compra usato + Export",
     "Multimarca, gamma media/pesante (MIG/TIG/MMA, arco sommerso, posizionatori)",
     "Bonifico rapido dopo accordo", "Organizzano loro il ritiro, anche in Europa",
     "Su preventivo; comprano a prezzo di mercato/ingrosso. Lotto = offerta migliore per pezzo",
     "Trustpilot 5/5 con ~745 recensioni; venditori segnalano buon prezzo, ritiro puntuale, pagamento veloce",
     "SI - ottimo per lotti; ritirano in Europa", "ALTA - multimarca, ritiro UE, pagamento rapido, recensioni eccellenti"],

    ["Sigma International S.r.l.", "Italia", "Pedrengo (BG)", "+39 035 657060",
     "info@sigmainternational.it", "sigmainternational.it", "Compra usato (permuta)",
     "MMA, MIG-MAG, TIG, plasma - rappresenta marchi leader", "Da concordare (valutazione permuta)",
     "Vicino (Nord Italia) - logistica corta", "Su preventivo / valore di permuta",
     "40+ anni di attivita, rivenditore strutturato; poche recensioni pubbliche online (chiedere referenze)",
     "SI (Nord Italia)", "ALTA per il Nord - permuta diretta; NOTA: vende anche nuovo (possibile concorrente)"],

    ["Eurosald S.r.l.", "Italia", "Onara di Tombolo (PD)", "+39 049 9485180",
     "info@eurosald.com", "eurosald.com", "Compra usato",
     "MIG, TIG, elettrodo; azienda saldatura/automazione/robotica", "Da concordare",
     "Vicino (Nord-Est) - logistica corta", "Su preventivo",
     "Azienda tecnica strutturata con sezione usato/occasioni; poche recensioni pubbliche (verificare acquisto da privati)",
     "Probabile (verificare)", "MEDIA-ALTA - confermare se acquista da privati e a che cifra"],

    ["Salfershop", "Italia", "Roma", "+39 06 94368820",
     "commerciale@salfershop.com", "salfershop.com", "Compra usato",
     "Saldatrici e attrezzatura usata varia", "Da concordare",
     "Centro Italia; magazzino ~1000 mq", "Su preventivo",
     "30+ anni, 80.000 prodotti, e-commerce affermato; servizio acquisto/vendita usato dichiarato (verificare ritiro lotti)",
     "Probabile (verificare)", "MEDIA-ALTA per il Centro - confermare ritiro lotti e prezzo"],

    ["Tecnogas S.r.l.", "Italia", "Modena", "+39 059 370870",
     "info@tecnogas-srl.it", "tecnogas-srl.it", "Compra usato",
     "Usato garantito, controllo e rigenerazione macchinari saldatura/taglio", "Da concordare",
     "Centro-Nord (Modena)", "Su preventivo",
     "Specializzata in rigenerazione usato; poche recensioni specifiche sul ramo usato online",
     "Probabile (verificare)", "MEDIA - confermare interesse a lotti e cifra"],

    ["Surplex GmbH", "Germania", "Dusseldorf", "+49 211 869 42600",
     "info@surplex.com", "surplex.com", "Asta / Export",
     "Macchinari industriali usati di ogni tipo (modello ad asta)", "Tramite asta/vendita, NON contante immediato",
     "Operano in tutta Europa, 15 filiali", "Valore d'asta (variabile)",
     "25+ anni, 200+ dipendenti; recensioni MISTE: bene servizio, ma lamentele su trasparenza condizioni e post-vendita (sito .de)",
     "Meglio per liquidazioni grandi", "MEDIA - modello asta, no pagamento immediato; adatto a volumi grandi"],

    ["Exapro", "Internazionale", "Marketplace UE", "-",
     "-", "exapro.com", "Marketplace",
     "Il cliente vende direttamente all'utilizzatore finale", "Tra le parti (no contante immediato dall'intermediario)",
     "Il venditore gestisce/concorda la spedizione", "Prezzo piu alto (quasi-retail) ma vendita non garantita",
     "Piattaforma B2B europea consolidata per macchine di saldatura usate",
     "Si ma richiede tempo", "MEDIA - massimo prezzo per il cliente, ma vende lui e non e immediato"],

    ["S.D. Nold Inc.", "Stati Uniti", "Lisbon, Ohio", "+1 330 424 3134",
     "jay@sdnoldinc.com", "sdnoldweldingsupplies.com", "Compra usato",
     "Miller e Lincoln (spec USA 60Hz) + altre marche", "Acquisto diretto (chiedere di Jay)",
     "USA - export transatlantico antieconomico per piccoli lotti", "Su preventivo (mercato USA)",
     "4.8/5 con 45 recensioni (Birdeye); attiva dal 1965, premi Lincoln; ottimo customer care",
     "NO per macchine italiane", "BASSA - macchine UE 50Hz non adatte al mercato USA 60Hz"],

    ["UWEL - Used Welding Equipment", "Stati Uniti", "Milford, Ohio", "-",
     "(form sul sito)", "usedweldingequipment.com", "Compra usato / Directory",
     "Surplus saldatrici (mercato USA 60Hz)", "Da concordare via form",
     "USA - stesso limite di spec/logistica", "Su preventivo (mercato USA)",
     "Portale storico USA per usato saldatura; contatto via form",
     "NO per macchine italiane", "BASSA - spec USA 60Hz, non adatto a macchine europee"],

    ["Industrial Discount", "Italia", "Aste / online", "(vedi sito)",
     "-", "industrialdiscount.it", "Aste / Marketplace",
     "Saldatrici usate da aziende/fallimenti via asta", "Via asta",
     "Aste con oltre 50 tribunali italiani", "Prezzo d'asta (variabile)",
     "Specializzato in aste giudiziarie industriali in Italia",
     "Indiretto (asta)", "MEDIA - utile come canale alternativo, non acquisto immediato"],

    ["Machineseeker.it", "Italia/UE", "Marketplace", "(vedi sito)",
     "-", "machineseeker.it", "Marketplace",
     "Il cliente pubblica MIG/MAG trifase usati", "Tra le parti",
     "Spedizione concordata tra le parti", "Prezzo richiesto dal venditore",
     "Grande marketplace europeo di macchine usate",
     "Si ma vende il cliente", "MEDIA - buon prezzo, ma vendita gestita dal cliente"],

    ["Subito.it", "Italia", "Annunci IT", "-",
     "-", "subito.it", "Marketplace",
     "Annunci privati/aziende di saldatrici usate", "Tra le parti",
     "Ritiro/spedizione tra le parti", "Prezzo richiesto dal venditore",
     "Piattaforma annunci piu diffusa in Italia",
     "Si per vendite locali", "MEDIA - veloce e locale, ma il cliente gestisce tutto"],
]

# Foglio note / metodo
NOTES = [
    ["SCHEDA RICERCA - Compratori di saldatrici usate per modello \"permuta indiretta\"", ""],
    ["Aggiornata", datetime.date.today().isoformat()],
    ["", ""],
    ["IL TUO MODELLO", "Vendi Miller/ESAB nuove. Il cliente vende le sue 3-5 MIG 300A usate (multimarca, funzionanti) direttamente a un intermediario, incassa, e con quei soldi + tuo sconto compra il nuovo. Tu NON ritiri/gestisci usato."],
    ["", ""],
    ["PREZZO - dato reale", "MIG 300A trifase usato di marca premium: riferimenti di mercato USA ~$1.500 (250A) - $3.250 (300A multiprocesso inverter). In UE indicativamente ~1.000-3.000 EUR a seconda di marca/eta/stato (valore di RIVENDITA al dettaglio)."],
    ["PREZZO - cosa pagano i buyer", "L'intermediario compra a prezzo di INGROSSO (tipicamente molto sotto il retail, deve rivendere con margine). La cifra esatta e SOLO su preventivo. Un LOTTO di 3-5 macchine = offerta per pezzo migliore e ritiro che conviene."],
    ["", ""],
    ["LEVA CHIAVE", "La marca decide il prezzo: premium (Miller, ESAB, Lincoln, Fronius, Cebora) = offerte buone; no-name = offerte basse."],
    ["TENSIONE / EXPORT", "Le macchine italiane sono 230/400V 50Hz: si rivendono in UE (Westermans, Surplex, intermediari IT). I buyer USA (S.D. Nold, UWEL) vogliono 60Hz -> non adatti."],
    ["", ""],
    ["AVVERTENZE", "1) Verifica sempre i contatti prima di trattare (dati pubblici, possono cambiare). 2) Pagamento immediato = preferisci bonifico, mai anticipi/commissioni a carico tuo. 3) Per export verifica P.IVA/VIES e identita azienda."],
    ["PROSSIMO PASSO CONSIGLIATO", "Per ogni operazione: prepara una scheda-lotto (marca, modello, n.serie, foto, stato), mandala a 2-3 buyer, prendi l'offerta migliore e usala come leva di vendita."],
    ["", ""],
    ["FONTI", "westermans.com/wanted.aspx; trustpilot.com/review/westermans.com; surplex.com; trustpilot/provenexpert Surplex; sigmainternational.it/usato; eurosald.com; salfershop.com/servizi; tecnogas-srl.it; sdnoldweldingsupplies.com + Birdeye; exapro.com; ebay/surplusrecord (prezzi MIG 300A)"],
]

def col_letter(n):
    s = ""
    while n >= 0:
        s = chr(n % 26 + 65) + s
        n = n // 26 - 1
    return s

def sheet_xml(rows, header_row=True, widths=None):
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">']
    if widths:
        out.append('<cols>')
        for i, w in enumerate(widths, start=1):
            out.append(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>')
        out.append('</cols>')
    out.append('<sheetData>')
    for r, row in enumerate(rows, start=1):
        out.append(f'<row r="{r}">')
        for c, val in enumerate(row):
            ref = f"{col_letter(c)}{r}"
            style = ' s="1"' if (header_row and r == 1) else ''
            out.append(f'<c r="{ref}"{style} t="inlineStr"><is><t xml:space="preserve">{esc(val)}</t></is></c>')
        out.append('</row>')
    out.append('</sheetData></worksheet>')
    return "".join(out)

content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>'''

root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

workbook = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>
<sheet name="Compratori" sheetId="1" r:id="rId1"/>
<sheet name="Note e Metodo" sheetId="2" r:id="rId2"/>
</sheets>
</workbook>'''

wb_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>
<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>
<fills count="3"><fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF2F4858"/></patternFill></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"><alignment wrapText="1" vertical="center"/></xf>
</cellXfs>
</styleSheet>'''

widths_main = [24, 14, 18, 18, 26, 24, 20, 32, 28, 28, 34, 44, 22, 40]
widths_notes = [26, 90]

with zipfile.ZipFile("saldatrici-usate-buyer.xlsx", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("_rels/.rels", root_rels)
    z.writestr("xl/workbook.xml", workbook)
    z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
    z.writestr("xl/styles.xml", styles)
    z.writestr("xl/worksheets/sheet1.xml", sheet_xml([HEADERS] + ROWS, True, widths_main))
    z.writestr("xl/worksheets/sheet2.xml", sheet_xml(NOTES, False, widths_notes))

print("OK - saldatrici-usate-buyer.xlsx creato")
