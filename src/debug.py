import code
import traceback
import signal

def _run_interpreter(sig, frame):
  d = {'_frame': frame}
  d.update(frame.f_globals)
  d.update(frame.f_locals)

  msg = 'Traceback:\n' + ''.join(traceback.format_stack(frame))

  c = code.InteractiveConsole(d)
  c.interact(msg)
  print 'Resuming.'

def setup_interrupt():
  signal.signal(signal.SIGUSR1, _run_interpreter)
