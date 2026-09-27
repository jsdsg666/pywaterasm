from importlib import resources

import pywaterasm.engine as engine


def test_package_imports_and_mapping_shipped():
    assert hasattr(engine, "main")
    assert resources.files("pywaterasm").joinpath("mapping.md").is_file()


def test_cli_help_exits_zero(capsys):
    try:
        engine.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("argparse --help should exit")
    out = capsys.readouterr().out
    assert ".inwt" in out