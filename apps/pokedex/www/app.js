// Load Pokemon data and render grid
async function loadPokemon() {
    try {
        const response = await fetch('/data/pokemon.json');
        const pokemonList = await response.json();
        
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
    
    card.appendChild(number);
    card.appendChild(sprite);
    card.appendChild(name);
    
    return card;
}

// Load Pokemon when page loads
document.addEventListener('DOMContentLoaded', loadPokemon);

