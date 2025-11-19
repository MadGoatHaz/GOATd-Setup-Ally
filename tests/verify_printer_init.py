from textual.app import App, ComposeResult
from GOATd.src.printer import PrinterSetup
import asyncio

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield PrinterSetup()

    async def on_mount(self):
        self.exit()

if __name__ == "__main__":
    try:
        app = TestApp()
        # Run the app in headless mode or just standard run which will exit immediately due to on_mount
        # We use a timeout just in case
        async def run_check():
            await app.run_async(headless=True, size=(80, 24))
            
        asyncio.run(run_check())
        print("PrinterSetup composed successfully (App ran and exited).")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"FAILED: {e}")