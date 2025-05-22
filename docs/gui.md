Using the GUI
=============

gpt-engineer ships with two graphical interfaces. The basic one is built with ``tkinter`` and provides a simple window for editing your prompt and running code generation. A more powerful web-based interface built with ``Flask`` exposes additional controls.

Launch
------

1. Create your project folder and add a ``prompt`` file just like when using the CLI.
2. Run ``gpte <project_dir> --gui`` for the Tk interface or ``gpte <project_dir> --advanced-gui`` to start the web UI.
   Use ``--advanced-gui-host`` and ``--advanced-gui-port`` to change the address.
3. A window opens where you can adjust settings and start the generation process.

Generated code will appear in ``<project_dir>/workspace`` as usual.

Capabilities
------------

- View or edit the loaded prompt before running.
- Toggle improve mode or standard generation.
- Set model name and temperature.
- Start and stop the run from the interface while monitoring logs.

Advanced GUI
------------

The advanced web interface adds controls for model selection, temperature, microservice generation and self-healing. A help panel explains each option and logs update in real time while the agent runs.
The Run button is automatically disabled while generation is in progress and a status indicator shows when the agent is busy.
