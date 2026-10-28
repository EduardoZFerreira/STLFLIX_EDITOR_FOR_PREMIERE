"""Tiny client for the FilmCraft control channel (127.0.0.1:9876)."""
import json
import os
import socket

SCRATCH = r"C:\Users\joaop\AppData\Local\Temp\claude\c--Users-joaop-OneDrive-Desktop-Filmcraft\22682de0-a379-4b3e-90c0-d90f8323b891\scratchpad"


TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".config", "filmcraft", "control_token")


def control_token():
    """FilmCraft >= 0.13 only starts the control server with FILMCRAFT_CONTROL_TOKEN (64 hex) and every request
    must carry it. The app is launched with the same token from this file."""
    tok = os.environ.get("FILMCRAFT_CONTROL_TOKEN")
    if not tok and os.path.exists(TOKEN_FILE):
        tok = open(TOKEN_FILE, encoding="ascii").read().strip()
    return tok


class FC:
    def __init__(self, port=9876):
        self.s = socket.create_connection(("127.0.0.1", port))
        self.f = self.s.makefile("rw", encoding="utf-8")
        self.n = 0
        self.token = control_token()

    def call(self, method, **params):
        self.n += 1
        req = {"id": self.n, "method": method, "params": params}
        if self.token:
            req["token"] = self.token
        self.f.write(json.dumps(req) + "\n")
        self.f.flush()
        r = json.loads(self.f.readline())
        if not r.get("ok"):
            raise RuntimeError(f"{method} {params}: {r.get('error')}")
        return r.get("result")

    def run(self, command, **params):
        return self.call("engine.execute", command=command, params=params)

    def shot(self, name, panel=None):
        p = {"path": f"{SCRATCH}\\{name}.png"}
        if panel:
            p["panel"] = panel
        return self.call("ui.screenshot", **p)

    def luma(self, seconds):
        """Compact scope summary at a sequence time: luma min/mean/max (%), saturation, hue, RGB means."""
        r = self.run("scopes.read", scopes=["waveform", "vectorscopeYuv"], seconds=seconds, columns=6, peaks=2)
        st = r["stats"]
        return {"y": [st["y"]["min"], st["y"]["mean"], st["y"]["max"]],
                "rgbMean": [st["r"]["mean"], st["g"]["mean"], st["b"]["mean"]],
                "sat": st["saturation"], "hue": st["hueDeg"]}
