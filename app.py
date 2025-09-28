from flask import Flask, jsonify, request, render_template
import random
import math

# Initialize the Flask application
app = Flask(__name__)

# --- In-memory "Database" for Player Saves ---
# In a real application, you would use a proper database like SQLite or Firestore.
# For this example, a dictionary will store each player's game state.
game_saves = {}

# --- Game Data Configuration (Constants) ---
REGIONS = {
    "Morogoro": {
        "specialty": "Rice and Maize farming.", "crops": ["Rice", "Maize", "Sunflower"], "livestock": ["Cattle", "Goats"]
    },
    "Arusha": {
        "specialty": "Horticulture and Coffee.", "crops": ["Coffee", "Tomatoes", "Flowers"], "livestock": ["Dairy Cattle"]
    },
    "Dodoma": {
        "specialty": "Grape and Sorghum cultivation.", "crops": ["Grapes", "Sorghum", "Millet"], "livestock": ["Goats", "Sheep"]
    }
}
CROP_DATA = { "Maize": {"growth_time": 5, "yield": 10} }

# --- Helper Functions ---
def get_simulated_nasa_data(region):
    return {
        "soil_moisture": round(random.uniform(0.2, 0.8), 2),
        "precipitation_forecast": random.choice(["clear", "light_rain", "heavy_rain"]),
        "vegetation_index": round(random.uniform(0.3, 0.9), 2)
    }

def initialize_game_state(player_name, region_name):
    """Creates a brand new game state for a new player."""
    return {
        "playerName": player_name,
        "region": region_name,
        "region_info": REGIONS.get(region_name),
        "currency": "TZS",
        "balance": 50000,
        "current_day": 1,
        "fields": [
            {"id": 1, "crop": None, "status": "Fallow", "water_level": 0.5, "growth_stage": 0, "health": 100},
            {"id": 2, "crop": None, "status": "Fallow", "water_level": 0.5, "growth_stage": 0, "health": 100}
        ],
        "livestock": [{"type": "Goats", "count": 5, "health": 90, "feed_level": 0.7}],
        "inventory": {"Maize Seed": 10, "Fertilizer": 5, "Goat Feed": 20, "Harvested Maize": 0},
        "active_quests": [{
            "id": "main_quest_1", "title": "Your First Farm",
            "description": f"Welcome to your farm in {region_name}! Let's get started by planting some maize. Select Field 1 and choose 'Plant'.",
            "learning_point": f"Choosing the right crop for your region is key to success. {region_name} is excellent for this.",
            "is_complete": False
        }],
        "market_prices": {"Harvested Maize": random.randint(500, 800)}
    }

def advance_day(player_state):
    """Simulates a day passing FOR A SPECIFIC PLAYER."""
    player_state['current_day'] += 1
    for item in player_state['market_prices']:
        player_state['market_prices'][item] = random.randint(500, 800)
    for field in player_state['fields']:
        if field['crop'] and field['status'] == 'Growing':
            if field['water_level'] > 0.4:
                field['growth_stage'] += 1
            field['water_level'] = max(0, field['water_level'] - 0.2)
            crop_info = CROP_DATA.get(field['crop'])
            if field['growth_stage'] >= crop_info['growth_time']:
                field['status'] = "Ready to Harvest"
    return player_state

# --- API Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/player', methods=['POST'])
def create_or_login_player():
    """Handles both creating a new player and logging in an existing one."""
    data = request.json
    player_name = data.get('playerName')
    
    if not player_name:
        return jsonify({"status": "error", "message": "Player name is required."}), 400

    # If player exists, log them in by returning their saved state
    if player_name in game_saves:
        player_state = game_saves[player_name]
        player_state["nasa_data"] = get_simulated_nasa_data(player_state.get("region"))
        return jsonify({"status": "success", "message": f"Welcome back, {player_name}!", "state": player_state})
    
    # If player does not exist, create a new one
    else:
        region = data.get('region', 'Morogoro')
        if region not in REGIONS:
            return jsonify({"status": "error", "message": "Invalid region selected."}), 400
        
        new_state = initialize_game_state(player_name, region)
        game_saves[player_name] = new_state
        new_state["nasa_data"] = get_simulated_nasa_data(region)
        return jsonify({"status": "success", "message": f"New farm created for {player_name} in {region}!", "state": new_state})

@app.route('/api/perform_action', methods=['POST'])
def perform_action():
    action_data = request.json
    player_name = action_data.get('playerName')

    if not player_name or player_name not in game_saves:
        return jsonify({"status": "error", "message": "Player not found."}), 404

    player_state = game_saves[player_name]
    action_type = action_data.get('action')
    params = action_data.get('params', {})
    
    message = "Action not recognized."
    success = False

    if action_type == 'next_day':
        player_state = advance_day(player_state)
        message = "A new day has dawned."
        success = True
    elif action_type == 'plant':
        field_id = params.get('field_id')
        crop_name = "Maize"
        seed_name = f"{crop_name} Seed"
        if player_state['inventory'].get(seed_name, 0) > 0:
            for field in player_state['fields']:
                if field['id'] == field_id and field['status'] == 'Fallow':
                    field['crop'] = crop_name
                    field['status'] = 'Growing'
                    field['growth_stage'] = 0
                    player_state['inventory'][seed_name] -= 1
                    message = f"You planted {crop_name} in Field {field_id}."
                    success = True
                    break
    elif action_type == 'water':
        field_id = params.get('field_id')
        for field in player_state['fields']:
            if field['id'] == field_id:
                field['water_level'] = min(1.0, field['water_level'] + 0.4)
                player_state['balance'] -= 100
                message = f"You watered Field {field_id}. It cost 100 TZS."
                success = True
                break
    elif action_type == 'harvest':
        field_id = params.get('field_id')
        for field in player_state['fields']:
            if field['id'] == field_id and field['status'] == 'Ready to Harvest':
                crop_name = field['crop']
                harvested_item = f"Harvested {crop_name}"
                crop_yield = CROP_DATA[crop_name]['yield']
                player_state['inventory'][harvested_item] = player_state['inventory'].get(harvested_item, 0) + crop_yield
                field['crop'] = None
                field['status'] = 'Fallow'
                field['growth_stage'] = 0
                message = f"You harvested {crop_yield} units of {crop_name}!"
                success = True
                break
        
    if success:
        game_saves[player_name] = player_state # Auto-save on every successful action
        return jsonify({"status": "success", "message": message, "new_state": player_state})
    else:
        return jsonify({"status": "error", "message": message}), 400

# This dummy endpoint is for the JS to fetch fresh NASA data after an action
@app.route('/api/game_state', methods=['GET'])
def get_game_state():
    # In a real scenario, this might take a player name, but for now, it's just for NASA data
    return jsonify({"nasa_data": get_simulated_nasa_data("Morogoro")})


if __name__ == '__main__':
    app.run(debug=True)

