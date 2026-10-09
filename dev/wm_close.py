"""Ask the window manager to close a window, like clicking its X button (_NET_CLOSE_WINDOW)."""
import sys, time
from Xlib import X, display, protocol
d = display.Display(); root = d.screen().root; wid = int(sys.argv[1])
ev = protocol.event.ClientMessage(window=d.create_resource_object("window", wid),
                                  client_type=d.intern_atom("_NET_CLOSE_WINDOW"), data=(32, [int(time.time()), 2, 0, 0, 0]))
root.send_event(ev, event_mask=X.SubstructureRedirectMask | X.SubstructureNotifyMask); d.flush()
