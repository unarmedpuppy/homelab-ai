#!/usr/bin/env python3
"""
Create a complete Pokemon list by fetching from PokeAPI or using a comprehensive list.
This script creates a JSON file with all Pokemon in National Pokedex order.
"""

import json
import os
import requests

def normalize_pokemon_name(name):
    """Convert Pokemon name to lowercase for sprite URL."""
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
    }
    
    if name in special_cases:
        return special_cases[name]
    
    normalized = name.lower()
    normalized = normalized.replace(" ", "-")
    normalized = normalized.replace("'", "")
    normalized = normalized.replace(".", "")
    normalized = normalized.replace(":", "")
    normalized = normalized.replace("♀", "-f")
    normalized = normalized.replace("♂", "-m")
    return normalized

def fetch_from_pokeapi():
    """Fetch all Pokemon from PokeAPI."""
    print("Fetching Pokemon list from PokeAPI...")
    pokemon_list = []
    
    # PokeAPI has 1025 Pokemon as of Gen 9
    for i in range(1, 1026):
        try:
            url = f"https://pokeapi.co/api/v2/pokemon/{i}/"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                name = data['name'].replace('-', ' ').title()
                # Handle special cases
                if name == "Nidoran F":
                    name = "Nidoran♀"
                elif name == "Nidoran M":
                    name = "Nidoran♂"
                elif name == "Farfetch D":
                    name = "Farfetch'd"
                elif name == "Mr Mime":
                    name = "Mr. Mime"
                elif name == "Mime Jr":
                    name = "Mime Jr."
                elif name == "Type Null":
                    name = "Type: Null"
                
                pokemon_list.append({
                    'number': i,
                    'name': name,
                    'sprite_name': normalize_pokemon_name(name)
                })
                print(f"  {i}: {name}")
            else:
                print(f"  Error fetching #{i}: HTTP {response.status_code}")
        except Exception as e:
            print(f"  Error fetching #{i}: {e}")
    
    return pokemon_list

def main():
    """Main function."""
    os.makedirs('data', exist_ok=True)
    
    print("Creating complete Pokemon list...")
    pokemon_list = fetch_from_pokeapi()
    
    json_path = 'data/pokemon.json'
    with open(json_path, 'w') as f:
        json.dump(pokemon_list, f, indent=2)
    
    print(f"\nGenerated Pokemon list with {len(pokemon_list)} Pokemon")
    print(f"Saved to {json_path}")

if __name__ == '__main__':
    main()

