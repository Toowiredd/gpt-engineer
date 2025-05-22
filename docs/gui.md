Using the GUI
gpt-engineer provides two graphical interfaces:

A basic interface built with tkinter for prompt editing and code generation.
An advanced web interface built with Flask offering enhanced controls and real-time logs.
Launch
Create a project folder and add a prompt file, as with CLI usage.
Start the interface:
For basic Tk GUI: gpte <project_dir> --gui
For advanced web UI: gpte <project_dir> --advanced-gui
Optional: Use --advanced-gui-host and --advanced-gui-port to set bind address and port.
The selected interface opens, allowing configuration and generation.
Generated code will appear in <project_dir>/workspace.

Capabilities
View and edit the prompt before execution.
Toggle between improve mode and standard generation.
Set model name and temperature.
Start/stop generation and monitor logs from the interface.
Generate boilerplate microservices via the Generate Microservice button.
Advanced GUI
Exposes additional controls for model selection, temperature, microservice generation, and self-healing.
Built-in help panel explains each option.
Logs update in real time during agent execution.
Run button is disabled while generation is active; status indicator shows agent activity.
Critical points:

Only start one interface per project directory to avoid state conflicts.
Always verify <project_dir>/workspace for output and rollback if generation fails.
For web UI, ensure chosen host/port are not already in use to prevent startup errors.
If the interface fails or becomes unresponsive, terminate the process and restart it after verifying no orphaned processes remain.