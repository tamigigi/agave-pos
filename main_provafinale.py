from flask import Flask, render_template, request, jsonify
import re

app = Flask(__name__)

# --- CONFIGURAZIONE ---
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
CODA_STAMPE = [] # La nuova coda per Pydroid

def determina_prezzo_base(prodotto):
    match = re.search(r'\((\d+\.\d+)€\)', prodotto)
    if match: return float(match.group(1))
    return 10.0

@app.route('/')
def home(): return render_template('palmare12.html', menu=MENU)

@app.route('/get_tavolo/<int:num>', methods=['GET'])
def get_tavolo(num):
    return jsonify(tavoli_stato.get(num, {}))

# --- NUOVA ROTTA PER PYDROID ---
@app.route('/prendi_stampa', methods=['GET'])
def prendi_stampa():
    if CODA_STAMPE:
        return jsonify(CODA_STAMPE.pop(0))
    return jsonify({}), 204

@app.route('/stampa/<int:num>', methods=['POST'])
def stampa(num):
    dest = request.args.get('dest', 'bar')
    ordine_tavolo = tavoli_stato[num]["ordine"]
    voci = [i for i in ordine_tavolo if i["reparto"] == dest and not i.get("stampato")]
    
    if not voci:
        return jsonify({"status": "Nessuna voce nuova"})

    testo = f"TAVOLO {num}\n----------------\n"
    for v in voci:
        testo += f"{v['prodotto']} {v['note']}\n"
        v["stampato"] = True
    
    # Inseriamo nella coda che Pydroid leggerà
    CODA_STAMPE.append({"reparto": dest, "corpo": testo})
    return jsonify({"status": f"Accodato per {dest}"})

@app.route('/add', methods=['POST'])
def add():
    # Mantieni invariato il tuo codice originale per /add
    data = request.json
    tavolo_num = int(data['tavolo'])
    prodotto_base = data['prodotto']
    reparto = "cucina" if prodotto_base in MENU["Aperitivo & Snack"] else "bar"
    tavoli_stato[tavolo_num]["ordine"].append({
        "prodotto": prodotto_base, "note": data.get('nota', ''), 
        "reparto": reparto, "stampato": False, "pagato": False
    })
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501, debug=True)
