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

def fetch_card_for_pokemon(pokemon_name, pokemon_number, max_retries=2):
    """Fetch the most valuable card for a Pokemon from TCG API."""
    # Try Pokedex number first (most accurate)
    try:
        url = f"{TCG_API_BASE}?q=nationalPokedexNumbers:{pokemon_number}&pageSize=250"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=15)
                
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
                
                break  # Success or 404, don't retry
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    raise
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                else:
                    raise
                    
    except Exception as e:
        # Fallback to name search only if Pokedex number fails
        name_var = normalize_pokemon_name_for_tcg(pokemon_name)
        try:
            url = f"{TCG_API_BASE}?q=name:{name_var}&pageSize=100"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                cards = data.get('data', [])
                
                if cards:
                    # Same priority logic
                    def card_priority(card):
                        rarity = card.get('rarity', '').lower()
                        priority = 0
                        if 'secret rare' in rarity:
                            priority += 2000
                        elif 'ultra rare' in rarity:
                            priority += 1500
                        elif 'rare' in rarity:
                            priority += 500
                        if card.get('images', {}).get('large'):
                            priority += 10
                        return priority
                    
                    cards.sort(key=card_priority, reverse=True)
                    best_card = cards[0]
                    card_image = best_card.get('images', {}).get('large') or best_card.get('images', {}).get('small')
                    
                    if card_image:
                        return {
                            'card_image': card_image,
                            'card_name': best_card.get('name', pokemon_name),
                            'set_name': best_card.get('set', {}).get('name', 'Unknown'),
                            'rarity': best_card.get('rarity', 'Unknown')
                        }
        except:
            pass
    
    return None

def main():
    """Main function to fetch card images for all Pokemon."""
    print("Fetching Pokemon card images from TCG API...")
    
    # Load Pokemon data
    with open('data/pokemon.json', 'r') as f:
        pokemon_list = json.load(f)
    
    # Load existing card data if it exists (for resume)
    output_file = 'data/cards.json'
    card_data = {}
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                card_data = json.load(f)
            print(f"Loaded {len(card_data)} existing card entries")
        except:
            pass
    
    total = len(pokemon_list)
    success_count = 0
    error_count = 0
    
    for i, pokemon in enumerate(pokemon_list, 1):
        pokemon_name = pokemon['name']
        pokemon_number = pokemon['number']
        
        # Skip if we already have this card
        if pokemon_number in card_data:
            continue
        
        print(f"  [{i}/{total}] Fetching card for {pokemon_name} (#{pokemon_number})...")
        
        try:
            card_info = fetch_card_for_pokemon(pokemon_name, pokemon_number)
            
            if card_info:
                card_data[pokemon_number] = card_info
                success_count += 1
                print(f"    ✓ Found: {card_info['card_name']} ({card_info['set_name']})")
            else:
                error_count += 1
                print(f"    ✗ No card found")
        except Exception as e:
            error_count += 1
            print(f"    ✗ Error: {e}")
        
        # Save progress every 10 Pokemon
        if i % 10 == 0:
            with open(output_file, 'w') as f:
                json.dump(card_data, f, indent=2)
            print(f"  [Progress saved: {len(card_data)}/{total} cards]")
        
        # Rate limiting - be nice to the API
        time.sleep(0.5)
    
    # Final save
    with open(output_file, 'w') as f:
        json.dump(card_data, f, indent=2)
    
    print(f"\n✓ Complete! Saved card data for {len(card_data)}/{total} Pokemon to {output_file}")
    print(f"  Success: {success_count}, Errors/Not found: {error_count}")

if __name__ == '__main__':
    main()

