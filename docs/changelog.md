# Changelog

## 0.2.0 (2026-05-23)

### Breaking changes
- Renamed internal ABCs to public names: `AbstractMask`, `AbstractStain`,
  `AbstractNoise` (were `_AbstractMask`, `_AbstractStain`, `_ABCNoise`)
- `_ABCNoise` now correctly inherits from `ABC`, so `_generate_noise` is
  enforced as abstract

### New features
- Sphinx + Furo documentation site
- Full test suite (60 tests across masks, stains, noise, and image)
- GitHub Actions CI: tests (Python 3.10/3.11/3.12) + lint + docs

### Fixes
- `Image.get_img`: stain normalisation now works on a `.copy()` of the stored
  array — repeated calls now return consistent results (was mutating in-place)
- `Image.plot`: fixed `cmap="grey"` → `cmap="gray"`

### Infrastructure
- Migrated from Poetry to **uv** + PEP 621 `pyproject.toml` (`hatchling` build backend)
- Replaced `black` + `isort` + `mypy` with **ruff** (lint + format)
- Python requirement relaxed from `^3.13` → `>=3.10`

---

## 0.1.0 (2024-11-29)

Initial release by [Hugh Warden](https://github.com/hwarden162).

- `Image`, `CircleMask`, `EllipseMask`, `ConstantStain`, `SpatialStain`, `ConstantNoise`
