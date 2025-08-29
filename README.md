# Monitoring System

This project provides a minimal client/server monitoring system.

## Project Structure

```
client/
    core/            # MonitoringAgent and coordination logic
    detectors/       # Hardware, software and backup detectors
    gui/             # System tray application and settings window
    utils/           # Helper utilities
    config/          # Client configuration handling
    main.py          # Entry point for the client

server/
    api/             # Flask blueprints
    models/          # SQLAlchemy models
    services/        # Business logic
    config/          # Server configuration
    app.py           # Flask application factory
```

## Development

Create a virtual environment and install dependencies:

```bash
pip install -r requirements/client.txt  # for client
pip install -r requirements/server.txt  # for server
```

Run tests with:

```bash
pytest
```

## Service Tag Detection

The monitoring agent now attempts to detect hardware service tags and related
serial numbers. Detection is performed using a priority of WMIC, PowerShell and
finally the Windows registry. Detected information is sent to the server and can
be queried via new API endpoints such as `/api/agents/service-tag/<tag>` or
searched using `/api/search?q=<query>`.
