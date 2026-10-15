"""ChatLink's desktop client. All socket operations run outside Tk's UI thread."""

import argparse
import queue
import socket
import threading
import tkinter as tk
from tkinter import font

BG, PANEL, FIELD = "#0C1420", "#152233", "#101B2A"
TEXT, MUTED, LINE = "#F1F6FC", "#9BAEC6", "#2B3D53"
MINT, VIOLET, RED = "#6AE4C0", "#BBA7FF", "#FFA4B3"


class ChatClient(tk.Tk):
    """Manage the connection, conversation display, and one pending message."""

    def __init__(self, host="127.0.0.1", port=5050):
        super().__init__()
        self.title("ChatLink — Simple TCP Chat")
        self.geometry("940x760")
        self.minsize(880, 700)
        self.configure(bg=BG)
        self.family = "Segoe UI" if "Segoe UI" in font.families() else "DejaVu Sans"
        self.host = tk.StringVar(value=host)
        self.port = tk.StringVar(value=str(port))
        self.message = tk.StringVar()
        self.sock = self.incoming = None
        self.busy = False
        self.generation = 0
        self.events = queue.Queue()
        self.build_ui()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.after(40, self.poll)

    def label(self, parent, text, size=11, color=TEXT, bold=False):
        """Use the same font and palette"""
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=(self.family, size, "bold" if bold else "normal"), anchor="w")

    def button(self, parent, text, command, primary=False):
        """Create a flat button with a visible keyboard focus border."""
        return tk.Button(parent, text=text, command=command, relief="flat", bd=0,
                         bg=MINT if primary else LINE, fg=BG if primary else TEXT,
                         activebackground="#8BEED2" if primary else "#3D526D",
                         activeforeground=BG if primary else TEXT, disabledforeground=MUTED,
                         font=(self.family, 11, "bold"), cursor="hand2", padx=20, pady=11,
                         highlightthickness=1, highlightbackground=LINE, highlightcolor=VIOLET)

    def entry(self, parent, variable, width=None):
        """Create a dark input with a colored border."""
        return tk.Entry(parent, textvariable=variable, width=width, relief="flat",
                        bg=FIELD, fg=TEXT, insertbackground=MINT, disabledbackground=FIELD,
                        disabledforeground=MUTED, highlightthickness=1,
                        highlightbackground=LINE, highlightcolor=MINT,
                        font=(self.family, 12))

    def build_ui(self):
        """Lay out of the conversation area and message composer"""
        page = tk.Frame(self, bg=BG, padx=30, pady=24)
        page.pack(fill="both", expand=True)
        header = tk.Frame(page, bg=BG)
        header.pack(fill="x")
        self.label(header, "C /", 25, MINT, True).pack(side="left")
        self.label(header, "  CHATLINK", 18, bold=True).pack(side="left")
        self.label(header, "PYTHON  /  TCP CHAT", 9, MUTED).pack(side="right")
        self.label(page, "One message. One reply.", 29, bold=True).pack(anchor="w", pady=(22, 7))
        self.label(page, "A conversation between your client window and the server terminal.", 11, MUTED).pack(anchor="w")
        endpoint = tk.Frame(page, bg=PANEL, padx=18, pady=14)
        endpoint.pack(fill="x", pady=(22, 16))
        fields = tk.Frame(endpoint, bg=PANEL)
        fields.pack(side="left", fill="x", expand=True)
        fields.columnconfigure(0, weight=1)
        self.label(fields, "SERVER ADDRESS", 9, MUTED, True).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.label(fields, "PORT", 9, MUTED, True).grid(row=0, column=1, sticky="w", padx=(12, 0), pady=(0, 6))
        self.host_input = self.entry(fields, self.host)
        self.host_input.grid(row=1, column=0, sticky="ew", ipady=8)
        self.port_input = self.entry(fields, self.port, 7)
        self.port_input.grid(row=1, column=1, padx=(12, 0), ipady=8)
        self.connect_button = self.button(endpoint, "Connect", self.toggle_connection, True)
        self.connect_button.pack(side="right", padx=(18, 0), anchor="s")

      
        self.label(page, "CSE 310  /  NETWORKING                                      CLIENT → SERVER → CLIENT", 9, MUTED).pack(side="bottom", anchor="w", pady=(14, 0))
        compose = tk.Frame(page, bg=BG)
        compose.pack(side="bottom", fill="x", pady=(14, 0))
        self.label(compose, "YOUR MESSAGE", 9, MUTED, True).pack(anchor="w", pady=(0, 7))
        row = tk.Frame(compose, bg=BG)
        row.pack(fill="x")
        self.message_input = self.entry(row, self.message)
        self.message_input.pack(side="left", fill="x", expand=True, ipady=11)
        self.message_input.bind("<Return>", lambda _: self.send())
        self.send_button = self.button(row, "Send  →", self.send, True)
        self.send_button.pack(side="right", padx=(12, 0))
        self.status = self.label(page, "●  Offline — start the server, then connect.", 10, MUTED)
        self.status.configure(wraplength=800, justify="left")
        self.status.pack(side="bottom", fill="x", pady=(8, 0))
        card = tk.Frame(page, bg=PANEL, padx=18, pady=16)
        card.pack(fill="both", expand=True)
        self.label(card, "CONVERSATION", 9, MUTED, True).pack(anchor="w", pady=(0, 12))
        history = tk.Frame(card, bg=PANEL)
        history.pack(fill="both", expand=True)
        scroll = tk.Scrollbar(history, bg=LINE, troughcolor=PANEL, relief="flat", bd=0, width=10)
        scroll.pack(side="right", fill="y")
        self.transcript = tk.Text(history, bg=PANEL, fg=TEXT, relief="flat", bd=0,
                                  highlightthickness=0, wrap="word", height=7,
                                  font=(self.family, 12), padx=2, pady=6,
                                  yscrollcommand=scroll.set, state="disabled", cursor="arrow")
        self.transcript.pack(side="left", fill="both", expand=True)
        self.transcript.bind("<Configure>", lambda _: self.transcript.see("end"))
        scroll.configure(command=self.transcript.yview)
        self.transcript.tag_configure("you", foreground=MINT, font=(self.family, 10, "bold"), spacing1=12)
        self.transcript.tag_configure("server", foreground=VIOLET, font=(self.family, 10, "bold"), spacing1=12)
        self.transcript.tag_configure("body", spacing1=5, spacing3=12)
        self.transcript.tag_configure("notice", foreground=MUTED, spacing1=8, spacing3=10)
        self.add_text("Connect to a server to start your conversation.\n", "notice")
        self.refresh_controls()

    def add_text(self, text, tag):
        """Append and scroll to the newest message"""
        self.transcript.configure(state="normal")
        self.transcript.insert("end", text, tag)
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def refresh_controls(self):
        """Allow one pending message."""
        connected = self.sock is not None
        self.connect_button.configure(text="Disconnect" if connected else "Connect",
                                      state="disabled" if self.busy and not connected else "normal")
        self.host_input.configure(state="disabled" if connected or self.busy else "normal")
        self.port_input.configure(state="disabled" if connected or self.busy else "normal")
        state = "normal" if connected and not self.busy else "disabled"
        self.message_input.configure(state=state)
        self.send_button.configure(state=state)

    def toggle_connection(self):
        """Prevents the window to freeze when unavailable server."""
        if self.sock is not None:
            self.disconnect()
            return
        if self.busy:
            return
        try:
            host, port = self.host.get().strip(), int(self.port.get())
            if not host or not 1 <= port <= 65535:
                raise ValueError
        except ValueError:
            self.status.configure(text="Enter a server address and a port from 1 to 65535.", fg=RED)
            return
        self.busy = True
        self.refresh_controls()
        self.status.configure(text="Connecting…", fg=MUTED)
        generation = self.generation

        def connect():
            try:
                sock = socket.create_connection((host, port), timeout=5)
                sock.settimeout(None)  # A person needs time to type the reply.
                incoming = sock.makefile("rb")
                self.events.put((generation, "connected", (sock, incoming)))
            except OSError:
                self.events.put((generation, "error", "Cannot reach the server. Check that server.py is running and the address and port match."))

        threading.Thread(target=connect, daemon=True).start()

    def send(self):
        """Send one UTF-8 message and read the newline-terminated server reply."""
        if self.sock is None or self.busy:
            return
        message = self.message.get().strip()
        if not 1 <= len(message) <= 2000 or "\n" in message or "\r" in message:
            self.status.configure(text="Enter one line with 1–2000 characters.", fg=RED)
            return
        self.add_text("YOU\n", "you")
        self.add_text(message + "\n", "body")
        self.message.set("")
        self.busy = True
        self.refresh_controls()
        self.status.configure(text="Waiting for a reply — type it in the server terminal and press Enter.", fg=VIOLET)
        generation, sock, incoming = self.generation, self.sock, self.incoming

        def exchange():
            try:
                sock.sendall((message + "\n").encode("utf-8"))
                raw = incoming.readline(8193)
                if not raw:
                    raise ConnectionError("The server closed the connection.")
                if len(raw) > 8192 or not raw.endswith(b"\n"):
                    raise ValueError("The server sent an invalid reply.")
                self.events.put((generation, "reply", raw.decode("utf-8").rstrip("\r\n")))
            except (OSError, ValueError) as exc:
                error_message = str(exc) if isinstance(exc, ValueError) else "The connection ended. Start the server and connect again."
                self.events.put((generation, "error", error_message))

        threading.Thread(target=exchange, daemon=True).start()

    def poll(self):
        """Apply queued network results"""
        try:
            while True:
                generation, kind, value = self.events.get_nowait()
                if generation != self.generation:
                    if kind == "connected":
                        value[1].close()
                        value[0].close()
                    continue
                self.busy = False
                if kind == "connected":
                    self.sock, self.incoming = value
                    self.add_text("Connected. Send a message to the server.\n", "notice")
                elif kind == "reply":
                    self.add_text("SERVER\n", "server")
                    self.add_text(value + "\n", "body")
                else:
                    self.disconnect()
                    self.status.configure(text=value, fg=RED)
                    continue
                self.status.configure(text=f"●  Connected to {self.host.get()}:{self.port.get()} — your turn.", fg=MINT)
                self.refresh_controls()
                self.message_input.focus_set()
        except queue.Empty:
            pass
        self.after(40, self.poll)

    def disconnect(self):
        """Unblock pending reads and close connection"""
        self.generation += 1
        sock, incoming = self.sock, self.incoming
        self.sock = self.incoming = None
        self.busy = False
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            def cleanup():
                incoming.close()
                sock.close()
            threading.Thread(target=cleanup, daemon=True).start()
            self.add_text("Disconnected.\n", "notice")
        self.status.configure(text="●  Offline — start the server, then connect.", fg=MUTED)
        self.refresh_controls()

    def close(self):
        """Close the desktop window."""
        self.disconnect()
        self.destroy()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChatLink graphical TCP client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()
    ChatClient(args.host, args.port).mainloop()
