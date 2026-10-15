# Overview

ChatLink is a simple Python chat application. I built it to learn how two programs connect and exchange messages through TCP sockets. To use it, run python server.py and python client.py in separate terminals. 

[Software Demo Video](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)

# Network Communication

ChatLink uses a client server model with TCP on port 5050. The client sends a message, and the server returns a reply. Messages use UTF-8 text. Both programs can run on the same computer using 127.0.0.1 (localhost).

# Development Environment

The software is written in **Python 3**. Visual Studio Code can be used to edit the source files, and separate terminals are used to run the server and client.

The application uses these Python standard-library modules:

* **socket:** Establishes TCP connections and sends and receives messages.
* **tkinter:** Creates the graphical client interface.
* **threading:** Runs network operations without freezing the interface.
* **queue:** Passes network results safely to the interface thread.
* **argparse:** Handles optional address and port settings.

No external pip packages are required. The Python installation must include Tkinter to run the graphical client.

# Useful Websites

* [Python Socket Documentation](https://docs.python.org/3/library/socket.html)
* [Python Socket Programming HOWTO](https://docs.python.org/3/howto/sockets.html)
* [Python Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
* [Python Threading Documentation](https://docs.python.org/3/library/threading.html)

# Future Work

* Add support for multiple clients communicating at the same time.
* Create a graphical interface for the server.
* Save conversation history to a local file.
