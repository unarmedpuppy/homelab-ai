#!/usr/bin/env python3
"""
Fetch Pokemon data from Serebii and download sprites.
This script scrapes the National Pokedex page and downloads all Pokemon sprites.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin

def normalize_pokemon_name(name):
    """Convert Pokemon name to lowercase for sprite URL."""
    # Handle special cases
    special_cases = {
        "Nidoran♀": "nidoran-f",
        "Nidoran♂": "nidoran-m",
        "Farfetch'd": "farfetchd",
        "Mr. Mime": "mr-mime",
        "Mime Jr.": "mime-jr",
        "Type: Null": "type-null",
        "Tapu Koko": "tapu-koko",
        "Tapu Lele": "tapu-lele",
        "Tapu Bulu": "tapu-bulu",
        "Tapu Fini": "tapu-fini",
        "Mr. Rime": "mr-rime",
        "Sirfetch'd": "sirfetchd",
        "Flabébé": "flabebe",
        "Hoopa Confined": "hoopa",
        "Hoopa Unbound": "hoopa-unbound",
        "Jangmo-o": "jangmo-o",
        "Hakamo-o": "hakamo-o",
        "Kommo-o": "kommo-o",
        "Type: Null": "type-null",
        "Necrozma": "necrozma",
        "Magearna": "magearna",
        "Marshadow": "marshadow",
        "Zeraora": "zeraora",
        "Meltan": "meltan",
        "Melmetal": "melmetal",
        "Grookey": "grookey",
        "Thwackey": "thwackey",
        "Rillaboom": "rillaboom",
        "Scorbunny": "scorbunny",
        "Raboot": "raboot",
        "Cinderace": "cinderace",
        "Sobble": "sobble",
        "Drizzile": "drizzile",
        "Inteleon": "inteleon",
        "Zacian": "zacian",
        "Zamazenta": "zamazenta",
        "Eternatus": "eternatus",
        "Kubfu": "kubfu",
        "Urshifu": "urshifu",
        "Zarude": "zarude",
        "Regieleki": "regieleki",
        "Regidrago": "regidrago",
        "Glastrier": "glastrier",
        "Spectrier": "spectrier",
        "Calyrex": "calyrex",
        "Wyrdeer": "wyrdeer",
        "Kleavor": "kleavor",
        "Ursaluna": "ursaluna",
        "Basculegion": "basculegion",
        "Sneasler": "sneasler",
        "Overqwil": "overqwil",
        "Enamorus": "enamorus",
        "Sprigatito": "sprigatito",
        "Floragato": "floragato",
        "Meowscarada": "meowscarada",
        "Fuecoco": "fuecoco",
        "Crocalor": "crocalor",
        "Skeledirge": "skeledirge",
        "Quaxly": "quaxly",
        "Quaxwell": "quaxwell",
        "Quaquaval": "quaquaval",
        "Lechonk": "lechonk",
        "Oinkologne": "oinkologne",
        "Tarountula": "tarountula",
        "Spidops": "spidops",
        "Nymble": "nymble",
        "Lokix": "lokix",
        "Pawmi": "pawmi",
        "Pawmo": "pawmo",
        "Pawmot": "pawmot",
        "Tandemaus": "tandemaus",
        "Maushold": "maushold",
        "Fidough": "fidough",
        "Dachsbun": "dachsbun",
        "Smoliv": "smoliv",
        "Dolliv": "dolliv",
        "Arboliva": "arboliva",
        "Squawkabilly": "squawkabilly",
        "Nacli": "nacli",
        "Naclstack": "naclstack",
        "Garganacl": "garganacl",
        "Charcadet": "charcadet",
        "Armarouge": "armarouge",
        "Ceruledge": "ceruledge",
        "Tadbulb": "tadbulb",
        "Bellibolt": "bellibolt",
        "Wattrel": "wattrel",
        "Kilowattrel": "kilowattrel",
        "Maschiff": "maschiff",
        "Mabosstiff": "mabosstiff",
        "Shroodle": "shroodle",
        "Grafaiai": "grafaiai",
        "Bramblin": "bramblin",
        "Brambleghast": "brambleghast",
        "Toedscool": "toedscool",
        "Toedscruel": "toedscruel",
        "Klawf": "klawf",
        "Capsakid": "capsakid",
        "Scovillain": "scovillain",
        "Rellor": "rellor",
        "Rabsca": "rabsca",
        "Flittle": "flittle",
        "Espathra": "espathra",
        "Tinkatink": "tinkatink",
        "Tinkatuff": "tinkatuff",
        "Tinkaton": "tinkaton",
        "Wiglett": "wiglett",
        "Wugtrio": "wugtrio",
        "Bombirdier": "bombirdier",
        "Finizen": "finizen",
        "Palafin": "palafin",
        "Varoom": "varoom",
        "Revavroom": "revavroom",
        "Cyclizar": "cyclizar",
        "Orthworm": "orthworm",
        "Glimmet": "glimmet",
        "Glimmora": "glimmora",
        "Greavard": "greavard",
        "Houndstone": "houndstone",
        "Flamigo": "flamigo",
        "Cetitan": "cetitan",
        "Cetoddle": "cetoddle",
        "Veluza": "veluza",
        "Dondozo": "dondozo",
        "Tatsugiri": "tatsugiri",
        "Annihilape": "annihilape",
        "Clodsire": "clodsire",
        "Farigiraf": "farigiraf",
        "Dudunsparce": "dudunsparce",
        "Kingambit": "kingambit",
        "Great Tusk": "great-tusk",
        "Scream Tail": "scream-tail",
        "Brute Bonnet": "brute-bonnet",
        "Flutter Mane": "flutter-mane",
        "Slither Wing": "slither-wing",
        "Sandy Shocks": "sandy-shocks",
        "Iron Treads": "iron-treads",
        "Iron Bundle": "iron-bundle",
        "Iron Hands": "iron-hands",
        "Iron Jugulis": "iron-jugulis",
        "Iron Moth": "iron-moth",
        "Iron Thorns": "iron-thorns",
        "Frigibax": "frigibax",
        "Arctibax": "arctibax",
        "Baxcalibur": "baxcalibur",
        "Gimmighoul": "gimmighoul",
        "Gholdengo": "gholdengo",
        "Wo-Chien": "wo-chien",
        "Chien-Pao": "chien-pao",
        "Ting-Lu": "ting-lu",
        "Chi-Yu": "chi-yu",
        "Roaring Moon": "roaring-moon",
        "Iron Valiant": "iron-valiant",
        "Koraidon": "koraidon",
        "Miraidon": "miraidon",
        "Walking Wake": "walking-wake",
        "Iron Leaves": "iron-leaves",
        "Dipplin": "dipplin",
        "Poltchageist": "poltchageist",
        "Sinistcha": "sinistcha",
        "Okidogi": "okidogi",
        "Munkidori": "munkidori",
        "Fezandipiti": "fezandipiti",
        "Ogerpon": "ogerpon",
        "Archaludon": "archaludon",
        "Hydrapple": "hydrapple",
        "Gouging Fire": "gouging-fire",
        "Raging Bolt": "raging-bolt",
        "Iron Boulder": "iron-boulder",
        "Iron Crown": "iron-crown",
        "Terapagos": "terapagos",
        "Pecharunt": "pecharunt",
    }
    
    if name in special_cases:
        return special_cases[name]
    
    # Default: lowercase, replace spaces and special chars with hyphens
    normalized = name.lower()
    normalized = normalized.replace(" ", "-")
    normalized = normalized.replace("'", "")
    normalized = normalized.replace(".", "")
    normalized = normalized.replace(":", "")
    normalized = normalized.replace("♀", "-f")
    normalized = normalized.replace("♂", "-m")
    return normalized

def fetch_pokemon_list():
    """Fetch Pokemon list from Serebii National Pokedex."""
    url = "https://www.serebii.net/pokemon/nationalpokedex.shtml"
    print(f"Fetching Pokemon list from {url}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    pokemon_list = []
    
    # Find all Pokemon entries in the table
    # The page has tables with Pokemon data
    tables = soup.find_all('table', class_='dextable')
    
    for table in tables:
        rows = table.find_all('tr')
        for row in rows[1:]:  # Skip header row
            cells = row.find_all('td')
            if len(cells) >= 3:
                # Extract number and name
                number_cell = cells[0]
                name_cell = cells[2]  # Usually the name is in the 3rd column
                
                # Get number
                number_text = number_cell.get_text(strip=True)
                if number_text and number_text.isdigit():
                    number = int(number_text)
                    
                    # Get name
                    name_link = name_cell.find('a')
                    if name_link:
                        name = name_link.get_text(strip=True)
                        if name:
                            pokemon_list.append({
                                'number': number,
                                'name': name
                            })
    
    # Sort by number
    pokemon_list.sort(key=lambda x: x['number'])
    
    print(f"Found {len(pokemon_list)} Pokemon")
    return pokemon_list

def download_sprite(pokemon_name, pokemon_number, output_dir):
    """Download a Pokemon sprite."""
    normalized_name = normalize_pokemon_name(pokemon_name)
    url = f"https://img.pokemondb.net/sprites/scarlet-violet/normal/{normalized_name}.png"
    
    output_path = os.path.join(output_dir, f"{pokemon_number:04d}_{normalized_name}.png")
    
    # Skip if already exists
    if os.path.exists(output_path):
        print(f"  ✓ {pokemon_name} (#{pokemon_number}) - already exists")
        return True
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"  ✓ {pokemon_name} (#{pokemon_number})")
            return True
        else:
            print(f"  ✗ {pokemon_name} (#{pokemon_number}) - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ {pokemon_name} (#{pokemon_number}) - Error: {e}")
        return False

def main():
    """Main function."""
    # Create directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('sprites', exist_ok=True)
    
    # Fetch Pokemon list
    pokemon_list = fetch_pokemon_list()
    
    # Save to JSON
    json_path = 'data/pokemon.json'
    with open(json_path, 'w') as f:
        json.dump(pokemon_list, f, indent=2)
    print(f"\nSaved Pokemon list to {json_path}")
    
    # Download sprites
    print(f"\nDownloading {len(pokemon_list)} sprites...")
    success_count = 0
    for pokemon in pokemon_list:
        if download_sprite(pokemon['name'], pokemon['number'], 'sprites'):
            success_count += 1
        time.sleep(0.1)  # Be nice to the server
    
    print(f"\nDownloaded {success_count}/{len(pokemon_list)} sprites")

if __name__ == '__main__':
    main()

