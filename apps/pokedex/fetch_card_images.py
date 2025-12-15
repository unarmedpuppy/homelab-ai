#!/usr/bin/env python3
"""
Fetch Pokemon TCG card images for each Pokemon.
Uses Pokemon TCG API to get the most valuable/rare card for each Pokemon.
"""

import json
import os
import requests
import time

# Pokemon TCG API - free tier allows 1000 requests/day
# For production, you'd want to cache results or use a different approach
TCG_API_BASE = "https://api.pokemontcg.io/v2/cards"

def normalize_pokemon_name_for_tcg(name):
    """Normalize Pokemon name for TCG API search."""
    # TCG API uses lowercase with hyphens
    normalized = name.lower()
    normalized = normalized.replace(" ", "-")
    normalized = normalized.replace("'", "")
    normalized = normalized.replace(".", "")
    normalized = normalized.replace(":", "")
    normalized = normalized.replace("♀", "-f")
    normalized = normalized.replace("♂", "-m")
    
    # Special cases for TCG API
    special_cases = {
        "nidoran-f": "nidoran♀",
        "nidoran-m": "nidoran♂",
        "farfetchd": "farfetch'd",
        "mr-mime": "mr. mime",
        "mime-jr": "mime jr.",
        "type-null": "type: null",
        "tapu-koko": "tapu koko",
        "tapu-lele": "tapu lele",
        "tapu-bulu": "tapu bulu",
        "tapu-fini": "tapu fini",
        "mr-rime": "mr. rime",
        "sirfetchd": "sirfetch'd",
    }
    
    if normalized in special_cases:
        return special_cases[normalized]
    
    return normalized

def fetch_card_for_pokemon(pokemon_name, pokemon_number):
    """Fetch the most valuable card for a Pokemon from TCG API."""
    # Try different name variations
    name_variations = [
        pokemon_name.lower(),
        normalize_pokemon_name_for_tcg(pokemon_name),
        pokemon_name.lower().replace("-", " "),
    ]
    
    for name_var in name_variations:
        try:
            # Search for cards by Pokemon name
            # Use nationalPokedexNumbers for more accurate matching
            url = f"{TCG_API_BASE}?q=nationalPokedexNumbers:{pokemon_number}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                cards = data.get('data', [])
                
                if not cards:
                    # Fallback to name search
                    url = f"{TCG_API_BASE}?q=name:{name_var}"
                    response = requests.get(url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        cards = data.get('data', [])
                
                if cards:
                    # Sort by rarity and value (prioritize ultra rare, secret rare, etc.)
                    def card_priority(card):
                        rarity = card.get('rarity', '').lower()
                        priority = 0
                        
                        # Rarity priority (most valuable first)
                        if 'secret rare' in rarity:
                            priority += 2000
                        elif 'ultra rare' in rarity:
                            priority += 1500
                        elif 'rainbow rare' in rarity:
                            priority += 1200
                        elif 'gold' in rarity or 'golden' in rarity:
                            priority += 1000
                        elif 'rare' in rarity and 'holo' in rarity.lower():
                            priority += 800
                        elif 'rare' in rarity:
                            priority += 500
                        elif 'uncommon' in rarity:
                            priority += 100
                        elif 'common' in rarity:
                            priority += 50
                        
                        # Prefer cards with high-res images
                        if card.get('images', {}).get('large'):
                            priority += 10
                        
                        # Check market price if available (from tcgplayer or cardmarket)
                        tcgplayer = card.get('tcgplayer', {})
                        if tcgplayer:
                            priority += 5
                        
                        return priority
                    
                    # Sort by priority (highest first)
                    cards.sort(key=card_priority, reverse=True)
                    
                    # Get the best card
                    best_card = cards[0]
                    # Use large/hires image if available, otherwise small
                    card_image = best_card.get('images', {}).get('large') or best_card.get('images', {}).get('small')
                    
                    if card_image:
                        return {
                            'card_image': card_image,
                            'card_name': best_card.get('name', pokemon_name),
                            'set_name': best_card.get('set', {}).get('name', 'Unknown'),
                            'rarity': best_card.get('rarity', 'Unknown')
                        }
            
            # Rate limiting - be nice to the API (free tier: 1000 requests/day)
            time.sleep(0.2)
            
        except Exception as e:
            print(f"  Error fetching card for {pokemon_name}: {e}")
            continue
    
    return None

def main():
    """Main function to fetch card images for all Pokemon."""
    print("Fetching Pokemon card images from TCG API...")
    
    # Load Pokemon data
    with open('data/pokemon.json', 'r') as f:
        pokemon_list = json.load(f)
    
    card_data = {}
    total = len(pokemon_list)
    
    for i, pokemon in enumerate(pokemon_list, 1):
        pokemon_name = pokemon['name']
        pokemon_number = pokemon['number']
        
        print(f"  [{i}/{total}] Fetching card for {pokemon_name} (#{pokemon_number})...")
        
        card_info = fetch_card_for_pokemon(pokemon_name, pokemon_number)
        
        if card_info:
            card_data[pokemon_number] = card_info
            print(f"    ✓ Found: {card_info['card_name']} ({card_info['set_name']})")
        else:
            print(f"    ✗ No card found")
        
        # Rate limiting - TCG API free tier is 1000 requests/day
        # So we'll be conservative
        if i % 10 == 0:
            time.sleep(1)
    
    # Save card data
    output_file = 'data/cards.json'
    with open(output_file, 'w') as f:
        json.dump(card_data, f, indent=2)
    
    print(f"\n✓ Saved card data for {len(card_data)} Pokemon to {output_file}")

if __name__ == '__main__':
    main()

