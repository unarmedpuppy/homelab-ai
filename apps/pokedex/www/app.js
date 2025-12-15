// Load Pokemon data and card data
let pokemonList = [];
let cardData = {};

// Load Pokemon data and render grid
async function loadPokemon() {
    try {
        // Load Pokemon data
        const pokemonResponse = await fetch('/data/pokemon.json');
        pokemonList = await pokemonResponse.json();
        
        // Load card data (if available)
        try {
            const cardResponse = await fetch('/data/cards.json');
            cardData = await cardResponse.json();
        } catch (error) {
            console.warn('Card data not available:', error);
            cardData = {};
        }
        
        const grid = document.getElementById('pokemon-grid');
        
        pokemonList.forEach(pokemon => {
            const card = createPokemonCard(pokemon);
            grid.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading Pokemon data:', error);
        document.getElementById('pokemon-grid').innerHTML = 
            '<p style="color: white; text-align: center; font-size: 1.5rem;">Error loading Pokemon data</p>';
    }
}

function createPokemonCard(pokemon) {
    const card = document.createElement('div');
    card.className = 'pokemon-card';
    card.dataset.pokemonNumber = pokemon.number;
    
    const inner = document.createElement('div');
    inner.className = 'pokemon-card-inner';
    
    // Front side (sprite)
    const front = document.createElement('div');
    front.className = 'pokemon-card-front';
    
    const number = document.createElement('div');
    number.className = 'pokemon-number';
    number.textContent = `#${pokemon.number.toString().padStart(3, '0')}`;
    
    const sprite = document.createElement('img');
    sprite.className = 'pokemon-sprite';
    const spriteName = pokemon.sprite_name || pokemon.name.toLowerCase().replace(/\s+/g, '-').replace(/'/g, '').replace(/\./g, '');
    sprite.src = `/sprites/${pokemon.number.toString().padStart(4, '0')}_${spriteName}.png`;
    sprite.alt = pokemon.name;
    sprite.onerror = function() {
        // Try alternative sprite name format
        const altName = pokemon.name.toLowerCase()
            .replace(/\s+/g, '-')
            .replace(/'/g, '')
            .replace(/\./g, '')
            .replace(/♀/g, '-f')
            .replace(/♂/g, '-m')
            .replace(/:/g, '');
        sprite.src = `/sprites/${pokemon.number.toString().padStart(4, '0')}_${altName}.png`;
        sprite.onerror = function() {
            card.classList.add('error');
        };
    };
    
    const name = document.createElement('div');
    name.className = 'pokemon-name';
    name.textContent = pokemon.name;
    
    front.appendChild(number);
    front.appendChild(sprite);
    front.appendChild(name);
    
    // Back side (card image) - fetch on demand
    const back = document.createElement('div');
    back.className = 'pokemon-card-back';
    back.innerHTML = '<div style="color: #666; padding: 20px;">Loading card...</div>';
    
    // Store loading state
    let cardLoaded = false;
    
    // Function to load card image
    const loadCardImage = async () => {
        if (cardLoaded) return;
        cardLoaded = true;
        
        try {
            // Try to fetch from local cards.json first
            const cardInfo = cardData[pokemon.number];
            if (cardInfo && cardInfo.card_image) {
                const cardImage = document.createElement('img');
                cardImage.className = 'pokemon-card-image';
                cardImage.alt = `${pokemon.name} TCG Card`;
                cardImage.src = cardInfo.card_image;
                cardImage.onerror = function() {
                    back.innerHTML = `<div style="color: #666; padding: 20px;">No card image available<br>for ${pokemon.name}</div>`;
                };
                back.innerHTML = '';
                back.appendChild(cardImage);
                return;
            }
            
            // Fallback: fetch from API on demand
            const response = await fetch(`https://api.pokemontcg.io/v2/cards?q=nationalPokedexNumbers:${pokemon.number}&pageSize=250`);
            const data = await response.json();
            const cards = data.data || [];
            
            if (cards.length > 0) {
                // Sort by rarity (prioritize rare cards)
                const sortedCards = cards.sort((a, b) => {
                    const aRarity = (a.rarity || '').toLowerCase();
                    const bRarity = (b.rarity || '').toLowerCase();
                    const rarityPriority = { 'secret rare': 3, 'ultra rare': 2, 'rare': 1, 'uncommon': 0, 'common': -1 };
                    const aPriority = rarityPriority[aRarity] || -2;
                    const bPriority = rarityPriority[bRarity] || -2;
                    return bPriority - aPriority;
                });
                
                const bestCard = sortedCards[0];
                const cardImage = bestCard.images?.large || bestCard.images?.small;
                
                if (cardImage) {
                    const img = document.createElement('img');
                    img.className = 'pokemon-card-image';
                    img.alt = `${pokemon.name} TCG Card`;
                    img.src = cardImage;
                    img.onerror = function() {
                        back.innerHTML = `<div style="color: #666; padding: 20px;">No card image available<br>for ${pokemon.name}</div>`;
                    };
                    back.innerHTML = '';
                    back.appendChild(img);
                } else {
                    back.innerHTML = `<div style="color: #666; padding: 20px;">No card image available<br>for ${pokemon.name}</div>`;
                }
            } else {
                back.innerHTML = `<div style="color: #666; padding: 20px;">No card found<br>for ${pokemon.name}</div>`;
            }
        } catch (error) {
            console.error(`Error loading card for ${pokemon.name}:`, error);
            back.innerHTML = `<div style="color: #666; padding: 20px;">Error loading card<br>for ${pokemon.name}</div>`;
        }
    };
    
    // Load card when card is flipped
    card.addEventListener('click', function() {
        if (!card.classList.contains('flipped')) {
            // About to flip - load card if not loaded
            loadCardImage();
        }
        card.classList.toggle('flipped');
    });
    
    inner.appendChild(front);
    inner.appendChild(back);
    card.appendChild(inner);
    
    return card;
}

// Load Pokemon when page loads
document.addEventListener('DOMContentLoaded', loadPokemon);

