from agent import run_agent, SYSTEM_PROMPT

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog
from textual.binding import Binding

class ResearchApp(App):

    BINDINGS = [
        Binding("ctrl+l", "clear_display", "Clear", priority=True),
        Binding("ctrl+k", "clear_history", "Reset", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    def compose(self) -> ComposeResult:

        yield Header()

        yield RichLog(
            id="log",
            wrap=True,
            markup=True
        )

        yield Input(
            placeholder="Ask a research question..."
        )

        yield Footer()

    def on_input_submitted(self, event):

        question = event.value.strip()

        if not question:
            return

        log = self.query_one("#log", RichLog)

        log.write(
            f"[bold blue]You:[/bold blue] {question}"
        )
        self.messages.append({
            "role": "user",
            "content": question
        })
        event.input.clear()

        self.run_worker(
            self._get_response(),
            thread=True
        )

    async def _get_response(self):

        log = self.query_one("#log", RichLog)

        try:
            answer = run_agent(self.messages)
            self.messages.append({
                "role": "assistant",
                "content": answer
            })

            self.call_from_thread(
                log.write,
                f"[bold green]Agent:[/bold green] {answer}"
            )

        except Exception as e:

            self.call_from_thread(
                log.write,
                f"[red]ERROR:[/red] {e}"
            )

    
    def action_clear_display(self):
        self.query_one("#log", RichLog).clear()
        
    def action_clear_history(self):
        self.messages.clear()
        self.messages.append({"role": "system", "content": SYSTEM_PROMPT})
        self.query_one("#log", RichLog).clear()

    def on_mount(self):
        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

if __name__ == "__main__":
    ResearchApp().run()