import json

from PIL import Image

from dorsos.cli import main


def test_generate_png_svg_and_config(tmp_path):
    assert main(["generate", "--preset", "rojo-estrellas", "--dpi", "60", "-o", str(tmp_path), "--save-config"]) == 0
    assert Image.open(tmp_path / "rojo-estrellas.png").size == (149, 208)
    assert (tmp_path / "rojo-estrellas.svg").read_text(encoding="utf-8").startswith("<svg")
    data = json.loads((tmp_path / "rojo-estrellas.json").read_text(encoding="utf-8"))
    assert data["pattern"]["kind"] == "rosetas"


def test_set_overrides_and_json_values(tmp_path):
    main(["generate", "--set", "frame.kind=geometrico", "--set", 'frame.options={"motif":"puntos"}',
          "--set", "style.density=0.9", "--dpi", "40", "--formats", "png", "-o", str(tmp_path),
          "--name", "x", "--save-config"])
    data = json.loads((tmp_path / "x.json").read_text(encoding="utf-8"))
    assert data["frame"]["options"]["motif"] == "puntos" and data["style"]["density"] == 0.9


def test_config_file_and_reproducibility(tmp_path):
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({"pattern": {"kind": "ondas"}, "seed": 3}), encoding="utf-8")
    for name in ("a", "b"):
        main(["generate", "--config", str(cfg), "--dpi", "40", "--formats", "png", "-o", str(tmp_path), "--name", name])
    assert (tmp_path / "a.png").read_bytes() == (tmp_path / "b.png").read_bytes()


def test_random_count_and_lock(tmp_path):
    main(["generate", "--random", "--seed", "10", "--count", "3", "--lock", "palette",
          "--set", "palette.background=#102030", "--dpi", "30", "--formats", "png", "-o", str(tmp_path),
          "--save-config"])
    names = sorted(p.name for p in tmp_path.glob("*.json"))
    assert names == ["dorso-10.json", "dorso-11.json", "dorso-12.json"]
    for n in names:
        assert json.loads((tmp_path / n).read_text(encoding="utf-8"))["palette"]["background"] == "#102030"


def test_bad_input_returns_error_code(tmp_path, capsys):
    assert main(["generate", "--preset", "no-existe", "-o", str(tmp_path)]) == 1
    assert "error" in capsys.readouterr().err


def test_sheet(tmp_path):
    out = tmp_path / "s.png"
    assert main(["sheet", "--presets", "--cols", "4", "--height", "120", "-o", str(out)]) == 0
    assert out.exists()
    assert main(["sheet", "--count", "4", "--seed", "1", "--height", "120", "-o", str(out)]) == 0


def test_presets_and_modules_listing(capsys):
    assert main(["presets"]) == 0 and main(["modules", "frame"]) == 0
    assert "geometrico" in capsys.readouterr().out


def test_sheet_catalog(tmp_path):
    out = tmp_path / "c.png"
    assert main(["sheet", "--catalog", "corners", "--cols", "3", "--height", "100", "-o", str(out)]) == 0
    assert out.exists()
