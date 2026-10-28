"""Conexão com o FilmCraft aberto (canal de controle JSON-lines em 127.0.0.1).

A partir da versão 0.13 o FilmCraft só liga o controle quando é aberto com a variável FILMCRAFT_CONTROL_TOKEN
(64 caracteres hexadecimais), e todo pedido precisa levar o mesmo token. O token fica em
~/.config/filmcraft/control_token; `abrir()` cria o token se ele não existir e abre o app com ele.
"""
import json
import os
import secrets
import socket
import subprocess
import time

TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".config", "filmcraft", "control_token")
EXE = os.environ.get("FILMCRAFT_EXE", r"C:\Program Files\FilmCraft\filmcraft.exe")
PORT = int(os.environ.get("FILMCRAFT_CONTROL_PORT", "9876"))


class FilmCraftError(RuntimeError):
    pass


def token(create=False):
    tok = os.environ.get("FILMCRAFT_CONTROL_TOKEN")
    if tok:
        return tok.strip()
    if not os.path.exists(TOKEN_FILE) and create:
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w", encoding="ascii") as f:
            f.write(secrets.token_hex(32))
    if os.path.exists(TOKEN_FILE):
        return open(TOKEN_FILE, encoding="ascii").read().strip()
    return None


def porta_aberta(port=PORT):
    try:
        socket.create_connection(("127.0.0.1", port), timeout=2).close()
        return True
    except OSError:
        return False


def abrir(projeto_fcproj=None, esperar_s=120):
    """Abre o FilmCraft com o controle ligado (e o projeto, se informado) e espera a porta responder."""
    if porta_aberta():
        return True
    env = dict(os.environ, FILMCRAFT_CONTROL_TOKEN=token(create=True))
    args = [EXE, "--control", str(PORT)] + ([projeto_fcproj] if projeto_fcproj else [])
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(args, env=env, creationflags=flags, close_fds=True)
    for _ in range(int(esperar_s / 2)):
        if porta_aberta():
            return True
        time.sleep(2)
    return False


class FC:
    """Cliente: fc.run("sequence.inspect", item=id) executa um comando do FilmCraft."""

    def __init__(self, port=PORT):
        try:
            self.s = socket.create_connection(("127.0.0.1", port))
        except OSError as e:
            raise FilmCraftError("FilmCraft sem controle ligado. Rode: python -m stlflix --projeto <pasta> abrir") from e
        self.f = self.s.makefile("rw", encoding="utf-8")
        self.n = 0
        self.tok = token()

    def call(self, method, **params):
        self.n += 1
        req = {"id": self.n, "method": method, "params": params}
        if self.tok:
            req["token"] = self.tok
        self.f.write(json.dumps(req) + "\n")
        self.f.flush()
        line = self.f.readline()
        if not line:
            raise FilmCraftError(f"{method}: conexão fechada pelo FilmCraft (token errado?)")
        r = json.loads(line)
        if not r.get("ok"):
            raise FilmCraftError(f"{method} {params}: {r.get('error')}")
        return r.get("result")

    def run(self, command, **params):
        return self.call("engine.execute", command=command, params=params)

    # atalhos usados em todo o kit ------------------------------------------------------------------------
    def sequencias(self):
        """{nome: id} de todas as sequências do projeto."""
        out = {}

        def walk(n):
            for c in n.get("children", []):
                if c.get("type") == "Sequence":
                    out[c["name"]] = c["item"]
                walk(c)
        walk(self.run("project.inspect")["root"])
        return out

    def itens_mov(self):
        """{nome do arquivo: id} dos .mov importados no projeto."""
        out = {}

        def walk(n):
            for c in n.get("children", []):
                if str(c.get("name", "")).lower().endswith(".mov"):
                    out[c["name"]] = c["item"]
                walk(c)
        walk(self.run("project.inspect")["root"])
        return out

    def seq(self, nome_ou_id):
        sid = nome_ou_id if isinstance(nome_ou_id, int) else self.sequencias()[nome_ou_id]
        return self.run("sequence.inspect", item=sid)

    def esperar_job(self, trecho_label, intervalo=3, timeout=7200):
        t0 = time.time()
        while time.time() - t0 < timeout:
            jobs = [j for j in self.run("jobs.list") if trecho_label in j["label"]]
            if jobs and jobs[-1].get("finished"):
                return jobs[-1]
            time.sleep(intervalo)
        raise FilmCraftError(f"job '{trecho_label}' não terminou em {timeout}s")
