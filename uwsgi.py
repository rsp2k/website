from webapp import create_app

app = create_app()
app.debug = True

if __name__ == "main":
    app.run()
