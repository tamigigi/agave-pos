from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

# --- MENU E CONFIGURAZIONE ---
MENU = {
    "Aperitivo & Snack": ["Tagliere Aperitivo (10.00€)", "Frittura Mista di Pesce (15.00€)", "Bustina di Patatine (2.00€)", "Nuggets di Pollo (6.00€)", "Frittura di Verdura (6.00€)", "Patatine Fritte (5.00€)"],
    "Cocktails (10.00€)": ["Mojito", "Mojito Cubano", "Rossini", "Negroni Sbagliato", "Americano", "Boulevardier", "Old Fashioned", "Gin Tonic", "Gin Lemon", "Negroni", "London Mule", "Gin Sour", "Long Island Ice Tea", "Rum Cooler", "Pina Colada", "Bellini", "Negrosky", "Vodka Tonic", "Vodka Lemon", "Vodka Sour", "Sex on the beach", "Mexican Mule", "Paloma", "Margarita", "Moscow Mule", "Cosmopolitan"],
    "Spritz (8.00€)": ["Aperol Spritz", "Campari Spritz", "Agave Spritz"],
    "Spritz Premium (10.00€)": ["Hugo Spritz"],
    "Analcolici (7.00€)": ["Virgin Colada", "Virgin Mojito", "Tropicana"],
    "Analcolici Premium (8.00€)": ["Tanqueray 0.0"],
    "Birre (5.00€)": ["Corona", "Corona zero", "Birra dello Stretto", "Ceres Bionda", "Tennent's", "Menabrea rossa", "Daura (gluten free)"],
    "Soft Drink": {"Acqua Naturale 0,5 lt": 2.0, "Acqua Frizzante 0,5 lt": 2.0, "Coca Cola": 3.0, "Coca Cola Zero": 3.0, "Fanta": 3.0, "Succo Pera/Pesca/Ace/Ananas": 3.0, "Schweppes Lemon": 3.0, "Acqua Tonica Schweppes": 3.0, "Acqua Tonica Mediterranean fever tree": 4.0, "Acqua Tonica Indian fever tree": 4.0, "Pinkgrapefruit Tonic fever tree": 4.0, "Ginger beer fever tree": 4.0},
    "I Nostri Gin (10.00€)": ["Gin Mare", "Gin del Professore", "Hendrick's", "Monkey 47", "Etna Gin", "Ionico", "Roku", "Malfy Pompelmo", "Amuerte", "Portofino", "Nordes", "J. Rose", "Tanqueray n. ten"],
    "I Nostri Rum (10.00€)": ["Kraken", "Zacapa 23", "Matusalem 23", "Havana 7", "Legendario"],
    "Le Nostre Vodka (10.00€)": ["Belvedere", "GreyGoose", "Beluga"],
    "Le Nostre Tequila (10.00€)": ["Patron Silver", "Patron Anejo", "Espolon Blanco", "Don Julio Silver", "Mezcal"],
    "I Nostri Whiskey (10.00€)": ["Oban 14 (12.00€)", "Jack Daniel's (6.00€)", "Four Roses (6.00€)", "Jack Daniel's Honey (6.00€)", "Jameson (6.00€)"],
    "Liquori & Amari (6.00€)": ["Fireball", "Pastis 51", "Limoncello", "Cointreau", "Sambuca", "Baileys", "Frangelico", "Drambuie", "Italicus", "Jägermeister", "Montenegro", "Amaro del Capo", "Amaro Amara", "Jefferson"],
    "Vini al Calice": {"Kikè (Calice)": 7.0, "Kebrilla (Calice)": 7.0, "Babbio (Calice)": 7.0, "Taurus (Calice)": 7.0, "Victora Rosato (Calice)": 7.0, "Etna Bianco DOC (Calice)": 8.0, "Prosecco (Calice)": 7.0},
    "Vini in Bottiglia": {"Kikè (Bottiglia)": 30.0, "Kebrilla (Bottiglia)": 30.0, "Babbio (Bottiglia)": 30.0, "Taurus (Bottiglia)": 30.0, "Victora Rosato (Bottiglia)": 30.0, "Etna Bianco DOC (Bottiglia)": 35.0, "Bottiglia di Prosecco": 30.0}
}

tavoli_stato = {i: {"ordine": [], "info": "", "gia_incassato_contanti": 0.0, "gia_incassato_carta": 0.0} for i in range(1, 101)}
REPARTI_PRODOTTI = {cat: "cucina" if cat == "Aperitivo & Snack" else "bar" for cat in MENU.keys()}
CODA_STAMPE = [] 

def determina_prezzo_base(prodotto):
    match = re.search(r'\((\d+\.\d+)€\)', prodotto)
    if match: return float(match.group(1))
    for cat, contenuto in MENU.items():
        if isinstance(contenuto, dict) and prodotto in contenuto: return contenuto[prodotto]
        if isinstance(contenuto, list) and prodotto in contenuto:
            if "12.00€" in prodotto: return 12.0
            if "6.00€" in prodotto: return 6.0
            if "10.00€" in cat: return 10.0
            if "8.00€" in cat: return 8.0
            if "7.00€" in cat: return 7.0
            if "6.00€" in cat: return 6.0
            if "5.00€" in cat: return 5.0
    return 10.0

# --- ROTTE PRINCIPALI ---
@app.route('/')
def home(): return render_template('palmare13.html', menu=MENU)

@app.route('/get_tavolo/<int:num>', methods=['GET'])
def get_tavolo(num):
    return jsonify(tavoli_stato.get(num, {"ordine": [], "info": "", "gia_incassato_contanti": 0.0, "gia_incassato_carta": 0.0}))

@app.route('/add', methods=['POST'])
def add():
    data = request.json
    tavolo_num = int(data['tavolo'])
    prodotto_base = data['prodotto']
    mixer = data.get('mixer', '')
    nota = data.get('nota', '')
    calici = int(data.get('calici', 0))
    quantita = int(data.get('quantita', 1))
    prezzo_pers = data.get('prezzo_personalizzato')
    pagato_subito = data.get('pagato_subito', False)
    metodo_subito = data.get('metodo_subito', 'NON PAGATO')
    
    nome_comanda = f"{prodotto_base} {mixer}".strip() if mixer else prodotto_base

    categoria_prodotto = "I Nostri Gin (10.00€)"
    for cat, cont in MENU.items():
        if (isinstance(cont, list) and prodotto_base in cont) or (isinstance(cont, dict) and prodotto_base in cont):
            categoria_prodotto = cat
            break

    if prezzo_pers is not None and prezzo_pers != "" and prezzo_pers != "null":
        prezzo_unitario = float(prezzo_pers)
    else:
        prezzo_unitario = determina_prezzo_base(prodotto_base)
        if mixer in ['Tonic', 'Lemon']:
            prezzo_unitario += 3.0
        if "Shot" in nota:
            prezzo_unitario = 3.0

    nota_corrente = nota
    if calici > 0:
        nota_corrente = f"{nota} | {calici} CALICI" if nota else f"{calici} CALICI"

    reparto_competenza = REPARTI_PRODOTTI.get(categoria_prodotto, "bar")
    
    # --- LOGICA DI RAGGRUPPAMENTO ---
    trovato = False
    for item in tavoli_stato[tavolo_num]["ordine"]:
        if item["prodotto"] == nome_comanda and item["note"] == nota_corrente and not item.get("pagato"):
            item["qta"] = item.get("qta", 1) + quantita
            item["prezzo"] = prezzo_unitario * item["qta"]
            trovato = True
            break
            
    if not trovato:
        tavoli_stato[tavolo_num]["ordine"].append({
            "prodotto": nome_comanda, 
            "qta": quantita, 
            "note": nota_corrente, 
            "prezzo": prezzo_unitario * quantita, 
            "pagato": pagato_subito, 
            "metodo": metodo_subito,
            "reparto": reparto_competenza, 
            "stampato": False
        })
        
    if pagato_subito:
        if metodo_subito == "CONTANTI":
            tavoli_stato[tavolo_num]["gia_incassato_contanti"] += (prezzo_unitario * quantita)
        elif metodo_subito == "CARTA":
            tavoli_stato[tavolo_num]["gia_incassato_carta"] += (prezzo_unitario * quantita)

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

# --- ROTTA PER SVUOTARE IL TAVOLO MANUALMENTE ---
@app.route('/svuota/<int:num>', methods=['POST'])
def svuota_tavolo_diretto(num):
    tavoli_stato[num] = {"ordine": [], "info": "", "gia_incassato_contanti": 0.0, "gia_incassato_carta": 0.0}
    return jsonify({"success": True, "status": "Tavolo svuotato e liberato"})

# --- ROTTE PER LA STAMPA MODIFICATA ---
@app.route('/prendi_stampa', methods=['GET'])
def prendi_stampa():
    if CODA_STAMPE:
        return jsonify(CODA_STAMPE.pop(0))
    return jsonify({}), 204

@app.route('/stampa/<int:num>', methods=['POST'])
def stampa(num):
    dest = request.args.get('dest', 'bar')
    ordine_tavolo = tavoli_stato[num]["ordine"]
    
    # --- NUOVA LOGICA CASSA (STAMPA TUTTO IL CONTO E SVUOTA) ---
    if dest == 'cassa':
        if not ordine_tavolo:
            return jsonify({"status": "Il tavolo e' vuoto!"})
            
        testo = f"  ** CONTO TAVOLO {num} **\n--------------------------------\n"
        totale_conto = 0.0
        
        for v in ordine_tavolo:
            qta = v.get('qta', 1)
            prezzo_riga = v.get('prezzo', 0.0)
            totale_conto += prezzo_riga
            testo += f"{qta}x {v['prodotto']}\n   {v['note']} -> {prezzo_riga:.2f} EUR\n"
            
        testo += "--------------------------------\n"
        testo += f" TOTALE CONTO: {totale_conto:.2f} EUR\n"
        testo += "--------------------------------\n\n\n\n\n"
        
        # Manda il conto alla coda della cassa
        CODA_STAMPE.append({"reparto": "cassa", "corpo": testo})
        
        # AZZERA E LIBERA IL TAVOLO IMMEDIATAMENTE
        tavoli_stato[num] = {"ordine": [], "info": "", "gia_incassato_contanti": 0.0, "gia_incassato_carta": 0.0}
        return jsonify({"status": "Conto inviato alla cassa. Tavolo Liberato!"})

    # --- LOGICA NORMALE PER BAR E CUCINA ---
    else:
        voci = [i for i in ordine_tavolo if i["reparto"] == dest and not i.get("stampato")]
        
        if not voci:
            return jsonify({"status": "Nessuna voce nuova"})

        testo = f"TAVOLO {num}\n----------------\n"
        for v in voci:
            qta = v.get('qta', 1)
            testo += f"{qta}x {v['prodotto']} {v['note']}\n"
            v["stampato"] = True
        
        CODA_STAMPE.append({"reparto": dest, "corpo": testo})
        return jsonify({"status": f"Accodato per {dest}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501, debug=True)
