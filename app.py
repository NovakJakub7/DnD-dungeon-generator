from dungeon_generator import create_app

# vytvořím instanci Flask aplikace
app = create_app()

# spustím aplikaci
if __name__ == "__main__":
    app.run(debug=True)