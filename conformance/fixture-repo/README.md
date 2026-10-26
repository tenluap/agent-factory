# Fixture repository for the factory's golden run

A tiny, throwaway project a golden run changes without consequence.

## Init (per golden run — always start from a fresh clone of this folder)

```sh
cp -R conformance/fixture-repo /tmp/golden-fixture && cd /tmp/golden-fixture
git init -q -b main . && git add -A && git -c user.name=golden -c user.email=golden@example commit -qm initial
git remote add throwaway /tmp/golden-throwaway.git   # bare repo: git init --bare /tmp/golden-throwaway.git
```

## Contents

- `src/greet.py` — one function; the run's feature changes it.
- `test_greet.py` — one test; the run's build/test commands: `python3 -m unittest discover -s .`
