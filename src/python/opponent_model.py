import numpy as np
import os
import json
import pickle
from sklearn.ensemble import RandomForestClassifier
from collections import defaultdict

class OpponentModel:
    """Model to predict opponent move probabilities."""
    
    def __init__(self, model_dir="models/opponent"):
        """Initialize the opponent model.
        
        Args:
            model_dir: Directory to store trained models
        """
        self.model_dir = model_dir
        self.models = {}  # Trained models
        self.move_encodings = {}  # Maps move IDs to indices
        self.move_reverse_encodings = {}  # Maps indices to move IDs
        
        # Create directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        
        # Try to load existing models if they exist
        if os.path.exists(os.path.join(model_dir, "general_model.pkl")):
            self._load_models()
    
    def train(self, data_dir="logs/battle_data"):
        """Train the model on collected battle data.
        
        Args:
            data_dir: Directory containing battle data files
            
        Returns:
            bool: True if training was successful, False otherwise
        """
        # Check if data directory exists
        if not os.path.exists(data_dir):
            print(f"Data directory {data_dir} does not exist.")
            return False
            
        # Load battle data
        try:
            battle_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
        except Exception as e:
            print(f"Error reading battle data directory: {e}")
            return False
        
        if not battle_files:
            print("No battle data found for training.")
            return False
        
        # Collect training data
        X = []  # Features
        y = []  # Target (opponent move)
        
        # Track all unique moves
        all_moves = set()
        
        # Process each battle file
        for filename in battle_files:
            try:
                filepath = os.path.join(data_dir, filename)
                with open(filepath, 'r') as f:
                    battle_data = json.load(f)
                
                # Skip battles with no turns
                if not battle_data.get("turns"):
                    continue
                    
                # Process each turn
                for i in range(len(battle_data["turns"]) - 1):  # Skip last turn
                    current_turn = battle_data["turns"][i]
                    next_turn = battle_data["turns"][i+1]
                    
                    # Skip turns with missing data
                    if not current_turn.get("opponent_active") or not next_turn.get("opponent_move"):
                        continue
                    
                    # Extract features
                    features = self._extract_features(current_turn)
                    
                    # Extract target (opponent's move)
                    opponent_move = next_turn["opponent_move"]["id"]
                    
                    # Add to training data
                    X.append(features)
                    y.append(opponent_move)
                    
                    # Add to unique moves
                    all_moves.add(opponent_move)
            except Exception as e:
                print(f"Error processing battle file {filename}: {e}")
                continue
        
        if not X:
            print("No usable training examples found.")
            return False
            
        # Create move encodings if not already created
        if not self.move_encodings:
            self.move_encodings = {move: i for i, move in enumerate(sorted(all_moves))}
            self.move_reverse_encodings = {i: move for move, i in self.move_encodings.items()}
            
            # Save encodings
            encoding_path = os.path.join(self.model_dir, "move_encodings.pkl")
            with open(encoding_path, 'wb') as f:
                pickle.dump((self.move_encodings, self.move_reverse_encodings), f)
        
        # Convert move IDs to indices
        y_encoded = [self.move_encodings.get(move, 0) for move in y]
        
        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y_encoded)
        
        # Save model
        self.models["general"] = model
        model_path = os.path.join(self.model_dir, "general_model.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
            
        print(f"Model trained on {len(X)} examples with {len(all_moves)} unique moves.")
        return True
    
    def predict_moves(self, battle, top_n=3):
        """Predict probabilities of opponent's next move.
        
        Args:
            battle: Current battle
            top_n: Number of top moves to return
            
        Returns:
            Dictionary of moves with probabilities
        """
        # If no model is trained yet, return uniform distribution
        if "general" not in self.models:
            return self._uniform_distribution(battle)
        
        try:
            # Extract features from current battle state
            features = self._extract_features_from_battle(battle)
            if not features:
                return self._uniform_distribution(battle)
            
            # Get model predictions
            probabilities = self.models["general"].predict_proba([features])[0]
            
            # Convert to move IDs with probabilities
            move_probs = {}
            for idx, prob in enumerate(probabilities):
                if idx in self.move_reverse_encodings:
                    move_id = self.move_reverse_encodings[idx]
                    move_probs[move_id] = prob
            
            # If opponent's known moves are limited, filter to those
            if battle.opponent_active_pokemon and hasattr(battle.opponent_active_pokemon, 'moves'):
                known_moves = set(battle.opponent_active_pokemon.moves.keys())
                if known_moves:
                    move_probs = {move: prob for move, prob in move_probs.items() if move in known_moves}
            
            # If we have no probabilities (e.g., all predicted moves are unknown), use uniform
            if not move_probs:
                return self._uniform_distribution(battle)
            
            # Normalize probabilities
            total_prob = sum(move_probs.values())
            if total_prob > 0:
                move_probs = {move: prob / total_prob for move, prob in move_probs.items()}
            
            # Return top N moves
            sorted_moves = sorted(move_probs.items(), key=lambda x: x[1], reverse=True)
            top_moves = dict(sorted_moves[:top_n])
            
            return top_moves
        except Exception as e:
            print(f"Error predicting moves: {e}")
            return self._uniform_distribution(battle)
    
    def _extract_features_from_battle(self, battle):
        """Extract features from a battle object.
        
        Args:
            battle: Battle object
            
        Returns:
            Feature vector
        """
        try:
            # Create a turn data structure similar to what we store
            turn_data = {
                "weather": str(battle.weather),
                "fields": [str(field) for field in battle.fields],
                "our_active": {
                    "species": battle.active_pokemon.species if battle.active_pokemon else "",
                    "types": [str(t) for t in battle.active_pokemon.types] if battle.active_pokemon else [],
                    "hp": battle.active_pokemon.current_hp_fraction if battle.active_pokemon else 0,
                },
                "opponent_active": {
                    "species": battle.opponent_active_pokemon.species if battle.opponent_active_pokemon else "",
                    "types": [str(t) for t in battle.opponent_active_pokemon.types] if battle.opponent_active_pokemon else [],
                    "hp": battle.opponent_active_pokemon.current_hp_fraction if battle.opponent_active_pokemon else 0,
                }
            }
            
            return self._extract_features(turn_data)
        except Exception as e:
            print(f"Error extracting features from battle: {e}")
            return []
    
    def _extract_features(self, turn_data):
        """Extract features from turn data.
        
        Args:
            turn_data: Dictionary containing turn information
            
        Returns:
            Feature vector
        """
        try:
            features = []
            
            # Weather (one-hot encoded)
            weather_types = ["clear", "raindance", "sunnyday", "sandstorm", "hail"]
            weather = turn_data.get("weather", "").lower()
            for w in weather_types:
                features.append(1 if w in weather else 0)
            
            # Our Pokémon HP percentage
            our_hp = turn_data.get("our_active", {}).get("hp", 1) 
            features.append(float(our_hp) if our_hp is not None else 1.0)
            
            # Opponent Pokémon HP percentage
            opp_hp = turn_data.get("opponent_active", {}).get("hp", 1)
            features.append(float(opp_hp) if opp_hp is not None else 1.0)
            
            # Type matchup (simplified)
            our_types = turn_data.get("our_active", {}).get("types", [])
            opp_types = turn_data.get("opponent_active", {}).get("types", [])
            
            # Add type matchup features (just presence of types for now)
            all_types = ["normal", "fire", "water", "electric", "grass", "ice", 
                         "fighting", "poison", "ground", "flying", "psychic", 
                         "bug", "rock", "ghost", "dragon", "dark", "steel", "fairy"]
            
            # Our types
            for t in all_types:
                features.append(1 if t in [str(type_).lower() for type_ in our_types] else 0)
                
            # Opponent types
            for t in all_types:
                features.append(1 if t in [str(type_).lower() for type_ in opp_types] else 0)
            
            return features
        except Exception as e:
            print(f"Error extracting features: {e}")
            return []
    
    def _uniform_distribution(self, battle):
        """Return uniform distribution over possible moves.
        
        Args:
            battle: Current battle
            
        Returns:
            Dictionary of moves with uniform probabilities
        """
        try:
            if battle.opponent_active_pokemon and hasattr(battle.opponent_active_pokemon, 'moves'):
                moves = list(battle.opponent_active_pokemon.moves.keys())
                if moves:
                    prob = 1.0 / len(moves)
                    return {move: prob for move in moves}
            
            # If no moves available, return empty dict
            return {}
        except Exception as e:
            print(f"Error generating uniform distribution: {e}")
            return {}
    
    def _load_models(self):
        """Load trained models from disk."""
        try:
            # Load move encodings
            encoding_path = os.path.join(self.model_dir, "move_encodings.pkl")
            if os.path.exists(encoding_path):
                with open(encoding_path, 'rb') as f:
                    self.move_encodings, self.move_reverse_encodings = pickle.load(f)
            
            # Load general model
            model_path = os.path.join(self.model_dir, "general_model.pkl")
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.models["general"] = pickle.load(f)
        except Exception as e:
            print(f"Error loading models: {e}")
            self.models = {}
            self.move_encodings = {}
            self.move_reverse_encodings = {}