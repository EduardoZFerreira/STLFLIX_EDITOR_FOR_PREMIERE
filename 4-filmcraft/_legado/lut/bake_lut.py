"""Bake the approved FilmCraft Hugo grade into a .cube for DaVinci Resolve.
A 16-bit HALD identity image (64^3 colours) goes through the exact grade in a throwaway headless FilmCraft
project (Lumetri: input LUT S-Log3/S-Gamut3.Cine -> Rec.709 + basic correction, values read from VSL-Hugo.fcproj);
the rendered frame becomes a 64-point 3D LUT. An identity pass (no effects) is rendered first to prove the still
goes through untouched (no colour-space conversion on import).
Usage: python bake_lut.py <out.cube>
"""
import json, os, subprocess, sys
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CLI = r"C:\Program Files\FilmCraft\filmcraft-cli.exe"
PROJ_SRC = r"C:\Users\joaop\OneDrive\Desktop\Filmcraft\VSL-Hugo.fcproj"
BAKE = os.path.join(HERE, "bake.fcproj")
HALD = os.path.join(HERE, "hald_in.png")
L = 8
N = L * L


def cli(*args, project=True, save=False):
    cmd = [CLI, "--compact"] + (["--project", BAKE] if project else []) + (["--save"] if save else []) + list(args)
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError(f"{args[:2]}: {r.stderr.strip()[:400]}")
    return r.stdout


def ex(command, params, save=True):
    out = cli("exec", command, json.dumps(params), save=save)
    return json.loads(out) if out.strip() else None


def hugo_lumetri():
    p = json.load(open(PROJ_SRC, encoding="utf-8"))
    v1 = p["project"]["items"]["14"]["kind"]["Sequence"]["video_tracks"][0]["items"]
    eff = next(e for c in v1 if c["name"].startswith("C23") for e in c["effects"] if e["effect"] == "lumetri")
    return {k: list(v["value"].values())[0] for k, v in eff["params"].items()}


def render(path):
    ex("file.exportFrame", {"path": path, "format": "png", "depth": 16, "target": "program", "time": 0}, save=False)
    img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    return img[..., :3][..., ::-1].astype(np.float64) / 65535.0   # BGR(A) -> RGB 0..1


def main(out_cube):
    # identity HALD (r fastest, then g, then b)
    idx = np.arange(N ** 3)
    ident = np.stack([idx % N, (idx // N) % N, idx // (N * N)], 1).astype(np.float64) / (N - 1)
    cv2.imwrite(HALD, (ident * 65535 + 0.5).astype(np.uint16).reshape(L ** 3, L ** 3, 3)[..., ::-1])
    if os.path.exists(BAKE):
        os.remove(BAKE)
    subprocess.run([CLI, "--compact", "--save-as", BAKE, "exec", "file.import", json.dumps({"paths": [HALD]})],
                   check=True, capture_output=True)
    proj = json.loads(cli("inspect", "project"))
    item = next(c["item"] for c in proj["root"]["children"] if c["name"].startswith("hald_in"))
    ex("file.newSequence", {"name": "bake", "width": L ** 3, "height": L ** 3, "fps": 23.976, "video": 1, "audio": 0})
    ex("timeline.place", {"item": item, "track": "V1", "time": 0, "insert": False, "audio": False})
    seq = json.loads(cli("inspect", "sequence"))
    clip = seq["video"][0]["items"][0]["clip"]

    ident_out = render(os.path.join(HERE, "hald_ident.png")).reshape(-1, 3)
    err = np.abs(ident_out - ident).max()
    print(f"passagem sem efeito: erro máx {err * 255:.2f}/255")
    if err > 2 / 255:
        sys.exit("a imagem não passa intacta (conversão de cor na importação) — LUT não seria fiel")

    lum = hugo_lumetri()
    ex("effects.apply", {"clips": [clip], "effect": "lumetri"})
    seq = json.loads(cli("inspect", "sequence"))
    effs = [e["effect"] for e in seq["video"][0]["items"][0]["effects"]]
    li = effs.index("lumetri")
    ex("lumetri.setInputLut", {"clip": clip, "lut": lum["input_lut"]})
    keys = ["temperature", "tint", "exposure", "contrast", "highlights", "shadows", "whites", "blacks", "saturation",
            "vibrance", "creative_sat", "faded_film", "sharpen", "vignette_amount"]
    for k in keys:
        ex("effects.setParam", {"clip": clip, "effect": li, "param": k, "value": lum[k]})
    seq = json.loads(cli("inspect", "sequence"))
    got = next(e for e in seq["video"][0]["items"][0]["effects"] if e["effect"] == "lumetri")["params"]
    print("lumetri aplicado:", {k: got[k]["value"] for k in ["input_lut"] + keys if k in got})

    graded = render(os.path.join(HERE, "hald_graded.png")).reshape(-1, 3)
    with open(out_cube, "w", encoding="ascii") as f:
        f.write('TITLE "VSL Hugo - grade B (FilmCraft)"\n')
        f.write("# S-Log3/S-Gamut3.Cine -> Rec.709 + temp -75, tint -20, exp +0.6, contrast 10, highlights -10, blacks -20, sat 85\n")
        f.write(f"LUT_3D_SIZE {N}\nDOMAIN_MIN 0.0 0.0 0.0\nDOMAIN_MAX 1.0 1.0 1.0\n")
        for r, g, b in graded:                                 # .cube order: red fastest = HALD order
            f.write(f"{r:.6f} {g:.6f} {b:.6f}\n")
    print("LUT salvo:", out_cube)


if __name__ == "__main__":
    main(sys.argv[1])
