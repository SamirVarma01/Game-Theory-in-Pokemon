from setuptools import setup, find_packages

setup(
    name="pokemon-game-theory-agent",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "poke-env>=0.5.0",
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "pybind11>=2.6.0",
    ],
    author="Samir Varma",
    author_email="sv773@scarletmail.rutgers.edu",
    description="A game theory-based Pokémon Showdown agent",
    keywords="pokemon, game theory, machine learning",
    python_requires=">=3.7",
)