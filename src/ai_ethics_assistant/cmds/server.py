from ai_ethics_assistant.configuration import Config
from ai_ethics_assistant.server.app import build_app

# Create configuration instance with development settings
config = Config(dev_mode=True)

# Build FastAPI application
app = build_app(config)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ai_ethics_assistant.cmds.server:app", host="0.0.0.0", port=8000, reload=True
    )
