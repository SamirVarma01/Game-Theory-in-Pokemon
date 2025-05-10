from opponent_model import OpponentModel

def main():
    """Train the opponent model on collected battle data."""
    model = OpponentModel()
    success = model.train()
    
    if success:
        print("Opponent model trained successfully!")
    else:
        print("Failed to train opponent model. Check if you have battle data.")

if __name__ == "__main__":
    main()