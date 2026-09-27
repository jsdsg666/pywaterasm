# pywaterasm

`pywaterasm` parses `.inwt` activated-sludge model definition files and generates standalone Python simulation scripts for single-tank or multi-tank A2O layouts.

## Install

```bash
pip install pywaterasm
```

The generator itself uses only the Python standard library. Generated simulation scripts use `numpy` and `scipy`; install them with:

```bash
pip install "pywaterasm[sim]"
```

## Usage

Command line:

```bash
pywaterasm input/ASM1.inwt -o generated_model/asm1_tank.py
# or
python -m pywaterasm input/ASM1.inwt -o generated_model/asm1_tank.py
```

Python API:

```python
from pathlib import Path
from pywaterasm.engine import parse_asm, validate, generate_py

model = parse_asm(Path("input/ASM1.inwt"))
validate(model)
code = generate_py(model, "ASM1.inwt")
Path("generated_model/asm1_tank.py").write_text(code, encoding="utf-8")
```

For multi-tank models, `pywaterasm.engine.generate_multi(model, asm_name)` returns a dictionary of generated file contents.

## Repository

- Source: https://github.com/jsdsg666/pywaterasm
- PyPI: https://pypi.org/project/pywaterasm/

## License

MIT. See `LICENSE`.