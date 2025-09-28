// Global variable to store the current player's name
let currentPlayerName = null;

// Use 'DOMContentLoaded' which fires as soon as the HTML is ready
document.addEventListener('DOMContentLoaded', () => {
    // --- SETUP LOGIN ---
    const startGameBtn = document.getElementById('start-game-btn');
    const playerNameInput = document.getElementById('player-name-input');
    const regionSelect = document.getElementById('region-select');
    const nextDayBtn = document.getElementById('next-day-btn');

    // This check prevents the 'addEventListener of null' error.
    if (startGameBtn) {
        startGameBtn.addEventListener('click', async () => {
            const playerName = playerNameInput.value.trim();
            if (!playerName) {
                alert("Please enter a name.");
                return;
            }
            
            const region = regionSelect.value;
            
            try {
                const response = await fetch('/api/player', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ playerName, region }),
                });
                const result = await response.json();
                
                if (result.status === 'success' && result.state) {
                    currentPlayerName = result.state.playerName;
                    document.getElementById('login-screen').classList.add('hidden');
                    document.getElementById('game-container').classList.remove('hidden');
                    renderGame(result.state);
                } else {
                    alert(`Error: ${result.message}`);
                }
            } catch (error) {
                console.error("Login/Create failed:", error);
                alert("Failed to connect to the server. Is it running?");
            }
        });
    } else {
        console.error("Fatal Error: The 'Start Farming' button was not found. Check the HTML file for an element with id='start-game-btn'.");
    }

    // --- SETUP GAME BUTTONS ---
    if (nextDayBtn) {
        nextDayBtn.addEventListener('click', () => {
            performAction('next_day');
        });
    } else {
        console.error("Fatal Error: The 'Next Day' button was not found. Check the HTML file for an element with id='next-day-btn'.");
    }
});


/**
 * Sends a player action to the backend. Now includes the playerName.
 * @param {string} action - The name of the action to perform.
 * @param {object} params - Additional parameters for the action.
 */
async function performAction(action, params = {}) {
    if (!currentPlayerName) {
        console.error("No player is logged in.");
        return;
    }

    try {
        const response = await fetch('/api/perform_action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action, params, playerName: currentPlayerName }),
        });
        
        const result = await response.json();
        
        if (result.status === 'success' && result.new_state) {
            renderGame(result.new_state);
        } else {
            alert(`Action failed: ${result.message}`);
        }
    } catch (error) {
        console.error("Could not perform action:", error);
    }
}

/**
 * Renders the entire game UI based on the current game state.
 * @param {object} state - The game state object from the backend.
 */
function renderGame(state) {
    if (!state) {
        console.error("Render failed: game state is null or undefined.");
        return;
    }
    
    // Update player and region info
    document.getElementById('player-name').textContent = state.playerName || 'N/A';
    document.getElementById('region-name').textContent = state.region || 'N/A';
    
    // Update top stats bar
    document.getElementById('current-day').textContent = state.current_day || 1;
    document.getElementById('balance').textContent = (state.balance || 0).toLocaleString();
    document.getElementById('currency').textContent = state.currency || 'TZS';

    // Update NASA data panel (with checks for undefined data)
    const nasa = state.nasa_data || {};
    document.getElementById('soil-moisture').textContent = `${(nasa.soil_moisture * 100 || 0).toFixed(0)}%`;
    document.getElementById('precipitation').textContent = (nasa.precipitation_forecast || 'N/A').replace('_', ' ');
    document.getElementById('vegetation-index').textContent = nasa.vegetation_index || 'N/A';
    
    // Render Fields
    const fieldsContainer = document.getElementById('fields-container');
    fieldsContainer.innerHTML = '';
    (state.fields || []).forEach(field => {
        const fieldCard = document.createElement('div');
        fieldCard.className = 'field-card';
        fieldCard.innerHTML = `<h4>Field ${field.id}</h4><p><strong>Crop:</strong> ${field.crop || 'None'}</p><p class="status"><strong>Status:</strong> ${field.status}</p><p><strong>Water:</strong> ${(field.water_level * 100).toFixed(0)}%</p><div class="action-buttons"></div>`;
        const actionButtons = fieldCard.querySelector('.action-buttons');
        if (field.status === 'Fallow') actionButtons.innerHTML += `<button onclick="performAction('plant', {field_id: ${field.id}})">Plant Maize</button>`;
        if (field.status === 'Growing') actionButtons.innerHTML += `<button onclick="performAction('water', {field_id: ${field.id}})">Water</button>`;
        if (field.status === 'Ready to Harvest') actionButtons.innerHTML += `<button onclick="performAction('harvest', {field_id: ${field.id}})">Harvest</button>`;
        fieldsContainer.appendChild(fieldCard);
    });

    // Render Quests
    const questsList = document.getElementById('quests-list');
    questsList.innerHTML = '';
    (state.active_quests || []).forEach(quest => {
        const questDiv = document.createElement('div');
        questDiv.className = `quest ${quest.is_complete ? 'complete' : ''}`;
        questDiv.innerHTML = `<strong>${quest.title}</strong><p>${quest.description}</p><p class="learning-point"><strong>Learning Point:</strong> ${quest.learning_point}</p>`;
        questsList.appendChild(questDiv);
    });

    // Render Inventory
    const inventoryList = document.getElementById('inventory-list');
    inventoryList.innerHTML = '';
    if (state.inventory) {
        for (const [item, quantity] of Object.entries(state.inventory)) {
            if (quantity > 0) {
                const li = document.createElement('li');
                li.innerHTML = `<span>${item}</span><span>${quantity}</span>`;
                inventoryList.appendChild(li);
            }
        }
    }
    
    // Render Market
    const marketList = document.getElementById('market-list');
    marketList.innerHTML = '';
     if (state.market_prices) {
        for (const [item, price] of Object.entries(state.market_prices)) {
             const li = document.createElement('li');
             li.innerHTML = `<span>${item}</span><span>${price.toLocaleString()} ${state.currency}</span>`;
             marketList.appendChild(li);
        }
     }
}

