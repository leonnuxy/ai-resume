from flask import Flask
import click

app = Flask(__name__)

@app.cli.command("check")
def check():
    """Custom check command."""
    click.echo("Check command executed successfully.")
