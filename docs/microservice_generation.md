# Microservice Generation

`gpt-engineer` can quickly scaffold a small Flask based microservice from a natural language prompt. This is useful for prototyping APIs without relying on the LLM for full code generation.

## CLI Usage

Provide a project directory containing a `prompt` file and pass the `--microservice` flag:

```bash
$ gpte my_service --microservice
```

The command will read the prompt file and create `app.py`, `Dockerfile` and `requirements.txt` inside the project directory.

## GUI Usage

Run the Tkinter GUI and click **Generate Microservice**. You will be prompted for the output directory and the prompt text.

```bash
$ python -m gpt_engineer.applications.gui.tk_gui
```
