import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import sleep

import typer
from click import BadParameter, MissingParameter
from revChatGPT.V1 import Chatbot
from rich.progress import Progress, SpinnerColumn, TextColumn

DATA_FOLDER = os.path.expanduser("~/.config")
KEY_FILE = Path(DATA_FOLDER) / "shell-gpt" / "api_key.txt"

config = {
    "Authorization": "<leave this as whatever - it will get replaced>",
    "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ik1UaEVOVUpHTkVNMVFURTRNMEZCTWpkQ05UZzVNRFUxUlRVd1FVSkRNRU13UmtGRVFrRXpSZyJ9.eyJodHRwczovL2FwaS5vcGVuYWkuY29tL3Byb2ZpbGUiOnsiZW1haWwiOiJuaWNvbGEucGFuZG9sZmkxNUBnbWFpbC5jb20iLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZ2VvaXBfY291bnRyeSI6IklUIn0sImh0dHBzOi8vYXBpLm9wZW5haS5jb20vYXV0aCI6eyJ1c2VyX2lkIjoidXNlci1vVFFWc2FEdm9nN0Z2UE5NM2laaTE1dDEifSwiaXNzIjoiaHR0cHM6Ly9hdXRoMC5vcGVuYWkuY29tLyIsInN1YiI6Imdvb2dsZS1vYXV0aDJ8MTA5MjYxOTgzMDI5ODYxNjU0ODk3IiwiYXVkIjpbImh0dHBzOi8vYXBpLm9wZW5haS5jb20vdjEiLCJodHRwczovL29wZW5haS5vcGVuYWkuYXV0aDBhcHAuY29tL3VzZXJpbmZvIl0sImlhdCI6MTY3NzIyOTkzNCwiZXhwIjoxNjc4NDM5NTM0LCJhenAiOiJUZEpJY2JlMTZXb1RIdE45NW55eXdoNUU0eU9vNkl0RyIsInNjb3BlIjoib3BlbmlkIHByb2ZpbGUgZW1haWwgbW9kZWwucmVhZCBtb2RlbC5yZXF1ZXN0IG9yZ2FuaXphdGlvbi5yZWFkIG9mZmxpbmVfYWNjZXNzIn0.fv5fB99KLFIOvaZ_phJHzB24y16YaiyexD-m8MMlDBhuVXU370h1zgWkgQI0bdeAjEMudvucsqVaVWqolYwIN_8_Pp58kfAhcECJTKaj2zKYdAc1H7OafSNMHOmizhwY95k3PeeGn590oO0b1CdJAnt-YH7c-SpBJ1Yvd-fWtyPMziaedNrXu6epH49JuYn7W3Ue4k4K4d88fByMmWoaGG9UhvbIm33qMWY5HQXXNadkk2cT0nbGaLmlXnYFUbnMgUih2vyc9iOa0nUJzLI-sR0TScyk2ucNBY76hHZDefOk7IcLVcGbqc07WvKv0ft3s6KDTAQ9Sskj0Z4LYTKa0Q",
}
chatbot = Chatbot(config, conversation_id=None)

def loading_spinner(func):
    def wrapper(*args, **kwargs):
        if not kwargs.pop("spinner", False):
            return func(*args, **kwargs)
        text = TextColumn("[green]Requesting OpenAI...")
        with Progress(SpinnerColumn(), text, transient=True) as progress:
            progress.add_task("request")
            return func(*args, **kwargs)

    return wrapper

def get_edited_prompt():
    with NamedTemporaryFile(suffix=".txt", delete=False) as file:
        # Create file and store path.
        file_path = file.name
    editor = os.environ.get("EDITOR", "vim")
    # This will write text to file using $EDITOR.
    os.system(f"{editor} {file_path}")
    # Read file when editor is closed.
    with open(file_path, "r") as file:
        output = file.read()
    os.remove(file_path)
    if not output:
        raise BadParameter("Couldn't get valid PROMPT from $EDITOR")
    return output

def typer_writer(text, code, shell, animate):
    shell_or_code = shell or code
    color = "magenta" if shell_or_code else None
    if animate and not shell_or_code:
        for char in text:
            typer.secho(char, nl=False, fg=color, bold=shell_or_code)
            sleep(0.015)
        # Add new line at the end, to prevent % from appearing.
        typer.echo("")
        return
    typer.secho(text, fg=color, bold=shell_or_code)

@loading_spinner
def openai_request(prompt):
    response = ''
    for data in chatbot.ask(prompt):
        response = data["message"]

    return response

# Using lambda to pass a function to default value, which make it apper as "dynamic" in help.
def main(
    prompt: str = typer.Argument(None, show_default=False, help="The prompt to generate completions for."),
    shell: bool = typer.Option(False, "--shell", "-s", help="Provide shell command as output."),
    execute: bool = typer.Option(False, "--execute", "-e", help="Will execute --shell command."),
    code: bool = typer.Option(False, help="Provide code as output."),
    editor: bool = typer.Option(False, help="Open $EDITOR to provide a prompt."),
    animation: bool = typer.Option(True, help="Typewriter animation."),
    spinner: bool = typer.Option(True, help="Show loading spinner during API request."),
):
    if not prompt and not editor:
        raise MissingParameter(param_hint="PROMPT", param_type="string")
    if shell:
        prompt = f"{prompt}. Provide only shell command as output."
    elif code:
        prompt = f"{prompt}. Provide only code as output."
    if editor:
        prompt = get_edited_prompt()
    response_text = openai_request(prompt)
    # For some reason OpenAI returns several leading/trailing white spaces.
    response_text = response_text.strip()
    typer_writer(response_text, code, shell, animation)
    if shell and execute and typer.confirm("Execute shell command?"):
        os.system(response_text)


def entry_point():
    typer.run(main)


if __name__ == "__main__":
    entry_point()
