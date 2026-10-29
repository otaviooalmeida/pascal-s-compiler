"""Executa os arquivos Pascal pela CLI e grava os logs reais para a entrega."""

from pathlib import Path
import subprocess
import sys

from fixture_cases import expected_exit

ROOT = Path(__file__).resolve().parent.parent


def main():
    output = ROOT / "tests/output"
    output.mkdir(exist_ok=True)
    failed = False
    for source in sorted((ROOT / "tests").glob("*.pas")):
        relative = source.relative_to(ROOT)
        result = subprocess.run([sys.executable, "yacc.py", str(relative)], cwd=ROOT,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, timeout=10)
        log = (f"$ .venv/bin/python yacc.py {relative}\n"
               f"{result.stdout}[exit code: {result.returncode}]\n")
        (output / f"{source.stem}.log").write_text(log, encoding="utf-8")
        expected = expected_exit(source)
        ok = result.returncode == expected and "Traceback" not in result.stdout
        ok = ok and (("Compilation succeeded." in result.stdout) == (expected == 0))
        failed |= not ok
        print(f"{'OK' if ok else 'FAIL'} {relative} (exit {result.returncode}, expected {expected})")
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
