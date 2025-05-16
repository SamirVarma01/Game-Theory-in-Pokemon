# Registeel - Pokémon Battle AI Project

Registeel is a sophisticated Pokémon battle AI project that combines multiple programming languages and technologies to create an intelligent battle system. The project includes both the battle AI implementation and a dashboard for monitoring and analysis.

## Project Structure

```
registeel/
├── src/
│   ├── python/         # Python implementation of the battle AI
│   ├── cpp/           # C++ components for performance-critical operations
│   └── csharp/        # C# dashboard for monitoring and analysis
│       └── PokemonDashboard/
├── models/            # Trained AI models and model-related files
├── data/             # Training data and battle logs
├── logs/             # Runtime logs and battle records
├── tests/            # Test suites for various components
└── build/            # Build artifacts and compiled binaries
```

## Components

### Python Battle AI
The core battle AI is implemented in Python using the `poke_env` library. This component handles:
- Battle state management
- Decision making
- Move selection
- Team building
- Training and evaluation

### C++ Components
Performance-critical operations are implemented in C++ for optimal execution speed.

### C# Dashboard
A modern dashboard application built in C# that provides:
- Real-time battle monitoring
- Performance analytics
- Team composition analysis
- Battle replay functionality

## Setup and Installation

### Prerequisites
- Python 3.8+
- .NET 6.0 or later
- C++ compiler (for building C++ components)
- Visual Studio 2022 (for C# development)

Please ensure that you have the Pokemon Showdown GitHub repository (https://github.com/smogon/pokemon-showdown) cloned onto your device for hosting local servers. If you would like to test the bot on the official showdown server, you can alter the server configuration accordingly. However, it is recommended to train on a local server.

### Python Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Building C++ Components
```bash
# Run the build script
./build_cpp.sh
```

### C# Dashboard Setup
1. Open `registeel.sln` in Visual Studio
2. Restore NuGet packages
3. Build the solution

## Usage

### Running the Battle AI
```bash
# Activate virtual environment
source venv/bin/activate

# Run the main script
python src/python/main.py
```

### Running the Dashboard
1. Open the solution in Visual Studio
2. Set PokemonDashboard as the startup project
3. Run the application

## Development

### Adding New Features
- Python components: Add new modules in `src/python/`
- C++ components: Add new files in `src/cpp/`
- C# dashboard: Add new features in `src/csharp/PokemonDashboard/`

### Testing
Run tests using the appropriate test runner for each component:
- Python: `pytest tests/python/`
- C#: Use Visual Studio's test explorer

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
[Add your license information here]

## Acknowledgments
- [poke_env](https://github.com/hsahovic/poke-env) for the Pokémon battle environment
- [Add other acknowledgments here] 