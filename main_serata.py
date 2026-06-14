from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# MENU REALE COMPLETO AGAVE ECO BAR
MENU = {
    "Aperitivo & Snack": ["Tagliere Aperitivo (10.00€)", "Frittura Mista di Pesce (15.00€)", "Bustina di Patatine (2.00€)", "Nuggets di Pollo (6.00€)", "Frittura di Verdura (6.00€)", "Patatine Fritte (5.00€)"],
    "Cocktails (10.00€)": ["Mojito", "Mojito Cubano", "Rossini", "Negroni Sbagliato", "Americano", "Boulevardier", "Old Fashioned", "Gin Tonic", "Gin Lemon", "Negroni", "London Mule", "Gin Sour", "Long Island Ice Tea", "Rum Cooler", "Pina Colada", "Bellini", "Negrosky", "Vodka Tonic", "Vodka Lemon", "Vodka Sour", "Sex on the beach", "Mexican Mule", "Paloma", "Margarita", "Moscow Mule", "Cosmopolitan"],
    "Spritz (8.00€)": ["Aperol Spritz", "Campari Spritz", "Agave Spritz"],
    "Spritz Premium (10.00€)": ["Hugo Spritz"],
    "Analcolici (7.00€)": ["Virgin Colada", "Virgin Mojito", "Tropicana"],
    "Analcolici Premium (8.00€)": ["Tanqueray 0.0"],
    "Birre (5.00€)": ["Corona", "Corona zero", "Birra dello Stretto", "Ceres Bionda", "Tennent's", "Menabrea rossa", "Daura (gluten free)"],
    "Soft Drink": {"Acqua Naturale 0,5 lt": 2.0, "Acqua Frizzante 0,5 lt": 2.0, "Coca Cola": 3.0, "Coca Cola Zero": 3.0, "Fanta": 3.0, "Succo Pera/Pesca/Ace/Ananas": 3.0, "Schweppes Lemon": 3.0, "Acqua Tonica Schweppes": 3.0, "Acqua Tonica Mediterranean fever tree": 4.0, "Acqua Tonica Indian fever tree": 4.0, "Pinkgrapefruit Tonic fever tree": 4.0, "Ginger beer fever tree": 4.0},
    "Whiskey & Distillati (6.00€)": ["Jack Daniel's", "Four Roses", "Jack Daniel's Honey", "Jameson"],
    "Liquori & Amari (6.00€)": ["Fireball", "Pastis 51", "Limoncello", "Cointreau", "Sambuca", "Baileys", "Frangelico", "Drambuie", "Italicus", "Jägermeister", "Montenegro", "Amaro del Capo", "Amaro Amara", "Jefferson"],
    "Distillati Premium (10.00€)": ["Oban 14 (8.00€)", "Belvedere", "GreyGoose", "Beluga", "Gin Mare", "Gin del Professore", "Hendrick's", "Monkey 47", "Etna Gin", "Ionico", "Roku", "Malfy Pompelmo", "Amuerte", "Portofino", "Nordes", "J. Rose", "Tanqueray n. ten", "Kraken", "Zacapa 23", "Matusalem 23", "Havana 7", "Legendario", "Patron Silver", "Patron Anejo", "Espolon Blanco", "Don Julio Silver", "Mezcal"],
    "Vini al Calice": {"Kikè (Calice)": 7.0, "Kebrilla (Calice)": 7.0, "Babbio (Calice)": 7.0, "Taurus (Calice)": 7.0, "Victora Rosato (Calice)": 7.0, "Etna Bianco DOC (Calice)": 8.0, "Prosecco (Calice)": 7.0},
    "Vini in Bottiglia": {"Kikè (Bottiglia)": 30.0, "Kebrilla (Bottiglia)": 30.0, "Babbio (Bottiglia)": 30.0, "Taurus (Bottiglia)": 30.0, "Victora Rosato (Bottiglia)": 30.0, "Etna Bianco DOC (Bottiglia)": 35.0, "Bottiglia di Prosecco": 30.0}
}

tavoli_stato = {i: {"ordine": [], "info": "", "gia_incassato_contanti": 0.0, "gia_incassato_carta": 0.0} for i in range(1, 101)}

REPARTI_PRODOTTI = {cat: "cucina" if cat == "Aperitivo & Snack" else "bar" for cat in MENU.keys()}

def determina_prezzo_base(prodotto):
    for cat, contenuto in MENU.items():
        if isinstance(contenuto, dict) and prodotto in contenuto: return contenuto[prodotto]
        if isinstance(contenuto, list) and prodotto in contenuto:
            if "10.00€" in cat: return 10.0
            if "8.00€" in cat: return 8.0
            if "7.00€" in cat: return 7.0
            if "6.00€" in cat: return 6.0
            if "5.00€" in cat: return 5.0
            if "15.00€" in prodotto: return 15.0
            if "35.00€" in prodotto: return 35.0
            if "30.00€" in prodotto: return 30.0
    return 10.0

@app.route('/')
def home(): return render_template('palmare.html', menu=MENU)

@app.route('/get_tavolo/<int:num>', methods=['GET'])
def get_tavolo(num):
    return jsonify(tavoli_stato.get(num, {"ordine": [], "info": "", "gia_incassato_contanti": 0.0, "gia_incassato_carta": 0.0}))

@app.route('/add', methods=['POST'])
def add():
    data = request.json
    tavolo_num = int(data['tavolo'])
    prodotto = data['prodotto']
    nota = data.get('nota', '')
    calici = data.get('calici', 0)
    quantita = int(data.get('quantita', 1))
    prezzo_pers = data.get('prezzo_personalizzato')
    pagato_subito = data.get('pagato_subito', False)
    metodo_subito = data.get('metodo_subito', 'NON PAGATO')
    
    categoria_prodotto = "Cocktails (10.00€)"
    for cat, cont in MENU.items():
        if (isinstance(cont, list) and prodotto in cont) or (isinstance(cont, dict) and prodotto in cont):
            categoria_prodotto = cat
            break

    prezzo_finale = float(prezzo_pers) if prezzo_pers else (3.0 if "Shot" in nota else determina_prezzo_base(prodotto))
    if calici > 0: nota = f"{nota} | {calici} CALICI" if nota else f"{calici} CALICI"
    reparto_competenza = REPARTI_PRODOTTI.get(categoria_prodotto, "bar")
        
    for _ in range(quantita):
        tavoli_stato[tavolo_num]["ordine"].append({
            "prodotto": prodotto, "note": nota, "prezzo": prezzo_finale, 
            "pagato": pagato_subito, "metodo": metodo_subito,
            "reparto": reparto_competenza, "stampato": False
        })
        if pagato_subito:
            if metodo_subito == "CONTANTI":
                tavoli_stato[tavolo_num]["gia_incassato_contanti"] += prezzo_finale
            elif metodo_subito == "CARTA":
                tavoli_stato[tavolo_num]["gia_incassato_carta"] += prezzo_finale

    return jsonify({"success": True})

@app.route('/salva_info/<int:num>', methods=['POST'])
def salva_info(num):
    tavoli_stato[num]["info"] = request.json.get("info", "")
    return jsonify({"success": True})

@app.route('/aggiorna_pagamento/<int:num>', methods=['POST'])
def aggiorna_pagamento(num):
    data = request.json
    tavoli_stato[num]["ordine"] = data.get("ordine", [])
    tavoli_stato[num]["gia_incassato_contanti"] = float(data.get("gia_incassato_contanti", 0.0))
    tavoli_stato[num]["gia_incassato_carta"] = float(data.get("gia_incassato_carta", 0.0))
    return jsonify({"success": True})

@app.route('/stampa/<int:num>', methods=['POST'])
def stampa(num):
    dest = request.args.get('dest', 'bar') # bar, cucina, cassa
    ordine_tavolo = tavoli_stato[num]["ordine"]
    voci_da_stampare = []
    
    # 1. Filtriamo le voci da stampare
    for item in ordine_tavolo:
        if dest == "cassa":
            # La cassa legge tutto per conoscenza o per conto finale
            voci_da_stampare.append(item)
        elif item["reparto"] == dest and not item["stampato"]:
            voci_da_stampare.append(item)
            item["stampato"] = True

    if not voci_da_stampare:
        return jsonify({"status": f"Nessuna voce nuova per {dest.upper()}"})

    # IP fisici: Cassa .204, Cucina .205, Bar .207
    ip_target = "192.168.1.204" if dest == "cassa" else ("192.168.1.207" if dest == "bar" else "192.168.1.205")
    
    print(f"\n--- INVIO COMANDA TAVOLO {num} A STAMPANTE {dest.upper()} ({ip_target}) ---")
    for v in voci_da_stampare:
        stato_pagamento = f"[{v['metodo']}]" if v['pagato'] else "[DA PAGARE]"
        print(f" -> 1x {v['prodotto']} {stato_pagamento} | Note: {v['note']}")
        
    # SE SIAMO IN SECONDA SERATA O INVIO DIRETTO: Se l'ordine è inviato al Bar/Cucina, spara in automatico una copia alla cassa per conoscenza
    if dest != "cassa":
        print(f"[AUTO-COPIA PER CONOSCENZA] Spedito duplicato comanda alla CASSA (192.168.1.204)")

    return jsonify({"status": f"Inviato a {dest.upper()} + Copia Cassa"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501, debug=True)

