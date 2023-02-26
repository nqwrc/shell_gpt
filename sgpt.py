import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep

import typer
from revChatGPT.V1 import Chatbot
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

DATA_FOLDER = os.path.expanduser("~/.config")
KEY_FILE = Path(DATA_FOLDER) / "shell-gpt" / "api_key.txt"

config = {
    "Authorization": "<leave this as whatever - it will get replaced>",
    "access_token": "YOUR_TOKEN_HERE",
}
chatbot = Chatbot(config, conversation_id=None)

app = typer.Typer()


def loading_spinner(func):
    def wrapper(*args, **kwargs):
        if not kwargs.pop("spinner", False):
            return func(*args, **kwargs)
        with Progress(
            SpinnerColumn(),
            TextColumn("[green]Requesting OpenAI..."),
            transient=True,
        ) as progress:
            task = progress.add_task("request")
            result = func(*args, **kwargs)
            progress.update(task, completed=True)
            return result

    return wrapper


def get_edited_prompt():
    with NamedTemporaryFile(suffix=".txt", delete=False) as file:
        file_path = file.name
    editor = os.environ.get("EDITOR", "vim")
    os.system(f"{editor} {file_path}")
    with open(file_path, "r") as file:
        output = file.read().strip()
    os.remove(file_path)
    if not output:
        raise typer.BadParameter("Couldn't get valid PROMPT from $EDITOR")
    return output


def typer_writer(text, code, shell, animate):
    console = Console()
    color = "magenta" if shell or code else None
    if animate and not shell and not code:
        for char in text:
            console.print(char, style=color, end="")
            sleep(0.015)
        console.print("")  # Add newline at the end.
        return
    console.print(text, style=color)


@loading_spinner
def openai_request(prompt):
    response = ""
    for data in chatbot.ask(prompt):
        response = data["message"]
    return response.strip()


@app.command()
def main(
    prompt: str = typer.Argument(
        None, show_default=False, help="The prompt to generate completions for."
    ),
    shell: bool = typer.Option(
        False, "--shell", "-s", help="Provide shell command as output."
    ),
    execute: bool = typer.Option(
        False, "--execute", "-e", help="Will execute --shell command."
    ),
    code: bool = typer.Option(False, help="Provide code as output."),
    editor: bool = typer.Option(
        False, "--editor", "-e", help="Open $EDITOR to provide a prompt."
    ),
    animation: bool = typer.Option(True, help="Typewriter animation."),
):
    if not prompt and not editor:
        raise typer.MissingParameter("PROMPT")
    if shell:
        prompt = f"{prompt}. Provide only shell command as output."
    elif code:
        prompt = f"{prompt}. Provide only code as output."
    if editor:
        prompt = get_edited_prompt()
    response_text = openai_request(prompt, spinner=animation)
    typer_writer(response_text, code, shell, animation)
    if shell and execute and Prompt.ask("Execute shell command?"):
        os.system(response_text)


if __name__ == "__main__":
    app()  # Call the Typer app instance instead of defining an entry point.