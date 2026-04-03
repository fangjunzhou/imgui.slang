import logging
import asyncio
from imgui_slang.example.app import ExampleApp

if __name__ == "__main__":
    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG)

    app = ExampleApp()
    asyncio.run(app.run())
