Using the GUI
=============

gpt-engineer ships with a lightweight graphical interface built with ``tkinter``. It provides a simple window for editing your prompt, choosing the model and running code generation.

Launch
------

1. Create your project folder and add a ``prompt`` file just like when using the CLI.
2. Run ``gpte <project_dir> --gui``.
3. A window opens where you can adjust settings and start the generation process.

Generated code will appear in ``<project_dir>/workspace`` as usual.

Capabilities
------------

- View or edit the loaded prompt before running.
- Toggle improve mode or standard generation.
- Set model name and temperature.
- Start and stop the run from the interface while monitoring logs.
