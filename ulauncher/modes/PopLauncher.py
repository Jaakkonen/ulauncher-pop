import json
from collections.abc import Callable

from gi.repository import Gio, GLib

from ulauncher.modes.poplauncher.poplauncher_ipc import PopRequest, PopResponse, TPopRequest, TPopResponse


class PopLauncherGLibImpl:
  """
  Starts PopLauncher process and gives functions to send requests to it
  and receive responses from it.

  Uses Glib for triggering read callbacks on the main thread and not
  be stuck in a blocking read call.
  """
  handler: Callable[[TPopResponse], None]
  stdin: Gio.OutputStream
  stdout: Gio.DataInputStream

  def __init__(self, response_callback: Callable[[TPopResponse], None]):
    self.handler = response_callback
    self.cancellable = Gio.Cancellable()
    flags = Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDIN_PIPE
    self.process = Gio.Subprocess.new(
      ["/usr/bin/pop-launcher"],
      flags
    )
    self.process.wait_check_async(
      cancellable=self.cancellable,
      callback=self._on_finished,
    )
    stdout = self.process.get_stdout_pipe()
    if stdout is None:
      errmsg = "Failed to create stdout pipe"
      raise RuntimeError(errmsg)
    self.stdout = Gio.DataInputStream.new(stdout)

    stdin = self.process.get_stdin_pipe()
    if stdin is None:
      errmsg = "Failed to create stdin pipe"
      raise RuntimeError(errmsg)
    self.stdin = stdin

    self._queue_read()

  def _on_finished(self, proc, results):
    """
    Callback triggered when the process finishes.
    """
    assert proc is self.process
    self.process.wait_check_finish(results)
    self.cancellable.cancel()

  def send_request(self, request: TPopRequest):
    """
    Send a request to the PopLauncher process.
    """
    # Write to self.process stdin
    text = request.to_json() + "\n"
    self.stdin.write_all(
      buffer=text.encode("utf-8"),
      cancellable=self.cancellable,
    )

  def _queue_read(self):
    """
    Queue a read callback on the main thread.
    """
    self.stdout.read_line_async(
      io_priority=GLib.PRIORITY_DEFAULT,
      cancellable=self.cancellable,
      callback=self._read_callback,
    )

  def _read_callback(self, _source, result: Gio.Task):
    """
    Read callback that is triggered when there is data to read.
    """
    assert _source is self.stdout

    line = None
    try:
      line, _length = self.stdout.read_line_finish_utf8(result)
      if line is None:
        errmsg = (
          "Tried reading from pop-launcher but got None. Did the process give EOF without cancelling the read task?"
        )
        raise RuntimeError(errmsg)
      try:
        response = PopResponse.from_json(line)
      except json.decoder.JSONDecodeError as e:
        e.add_note(f"Invalid output from pop-launcher. Expected JSON, received: {line}")
        raise e
      try:
        self.handler(response)
      except Exception as e:
        e.add_note(f"Error handling response from pop-launcher: {response}")
        raise e
    finally:
      self._queue_read()


class PopLauncherProvider:
  """
  PopLauncherProvider is a class that provides a list of results and
  implements the "ResultProvider" protocol.
  """
  on_response: Callable[[TPopResponse], None]

  def __init__(self, on_response: Callable[[TPopResponse], None]):
    self.on_response = on_response
    # Start the `pop-launcher` process and get pipes to stdin and stdout.
    self.glib_impl = PopLauncherGLibImpl(self.on_response)

  def on_query_change(self, query: str) -> None:
      """
      Triggered when user changes the query text.
      Returns a list of results.
      """
      self.glib_impl.send_request(PopRequest.Search(query))

  def on_enter(self, id: int) -> None:
      """
      Triggered when user presses enter.
      """
      self.glib_impl.send_request(PopRequest.Activate(id))
