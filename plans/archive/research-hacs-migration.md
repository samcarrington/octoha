# HACS Repository Structure Migration - Research Findings

## Research Summary

This research analyzes the current Octoha repository structure and identifies the changes needed to make it HACS compliant for publication in the Home Assistant Community Store.

## Current Repository Structure Analysis

### Integration Location
- **Current path**: `src/custom_components/octoha/`
- **Integration domain**: `octoha`
- **Integration name**: "Octoha - Octopus Energy"

### Complete Current Structure

#### Root Directory
```
/Users/Scarring/dev/octopus-ha/
├── README.md (✓ HACS compatible)
├── LICENSE (✓ HACS compatible) 
├── CHANGELOG.md (✓ HACS compatible)
├── pyproject.toml (build configuration)
├── .gitignore
├── src/
│   └── custom_components/
│       └── octoha/  ← INTEGRATION FILES HERE
├── tests/ (255+ test files - comprehensive coverage)
├── docs/ (documentation files)
├── plans/ (planning documents)
└── .github/ (GitHub workflows and templates)
```

#### Integration Files (src/custom_components/octoha/)
```
octoha/
├── __init__.py (✓)
├── manifest.json (✓ valid HA integration manifest)
├── config_flow.py (✓)
├── diagnostics.py (✓)
├── sensor.py (✓)
├── binary_sensor.py (✓)
├── coordinator.py (✓)
├── const.py (✓)
├── events.py (✓)
├── strings.json (✓ translations)
├── translations/
│   └── en.json (✓ English translations)
├── api/
│   ├── __init__.py
│   ├── auth.py
│   ├── client.py
│   ├── exceptions.py
│   ├── graphql.py
│   └── rest.py
└── models/
    ├── __init__.py
    ├── account.py
    ├── consumption.py
    ├── dispatch.py
    └── tariff.py
```

### Integration Details

#### manifest.json Analysis
```json
{
  "domain": "octoha",
  "name": "Octoha - Octopus Energy",
  "codeowners": ["@samcarrington"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/samcarrington/octoha",
  "iot_class": "cloud_polling", 
  "issue_tracker": "https://github.com/samcarrington/octoha/issues",
  "requirements": [],
  "version": "0.1.0"
}
```

#### Key Features
- Full Home Assistant integration with config flow
- Sensors, binary sensors, and automation events
- Diagnostics support  
- Translations (EN)
- Comprehensive test coverage (255+ tests)
- Proper HA integration patterns

## HACS Requirements Analysis

Based on HACS documentation and common patterns in the community:

### Required Files (✓ = Present, ✗ = Missing, ⚠ = Needs Change)

#### Repository Root Requirements
- ✓ **README.md** - Comprehensive documentation present
- ✓ **LICENSE** - MIT license present
- ⚠ **Custom components directory structure** - Currently in `src/custom_components/`, needs to be in root `custom_components/`
- ⚠ **hacs.json** - Missing HACS metadata file
- ✗ **info.md** - Optional but recommended short description

#### Integration Directory Requirements  
- ✓ **manifest.json** - Valid and complete
- ✓ **__init__.py** - Integration setup
- ✓ **config_flow.py** - Configuration flow
- ✓ **All platform files** - sensor.py, binary_sensor.py
- ✓ **strings.json** - Translations metadata
- ✓ **translations/** - Language files

### HACS Structure Requirements

#### Standard HACS Directory Structure
```
repository-root/
├── README.md
├── LICENSE  
├── hacs.json          ← MISSING
├── info.md            ← MISSING (optional)
└── custom_components/  ← NEEDS TO MOVE FROM src/
    └── octoha/
        ├── manifest.json
        ├── __init__.py
        ├── config_flow.py
        └── [all other integration files...]
```

## Gap Analysis

### Critical Changes Required

1. **Move Integration Files** 
   - **Current**: `src/custom_components/octoha/`
   - **Required**: `custom_components/octoha/`
   - **Impact**: High - Core requirement for HACS discovery

2. **Create hacs.json**
   - **Status**: Missing
   - **Purpose**: HACS metadata for categorization and display
   - **Impact**: High - Required for HACS publication

3. **Create info.md** 
   - **Status**: Missing  
   - **Purpose**: Short integration description for HACS UI
   - **Impact**: Medium - Improves user experience

4. **Update Build Configuration**
   - **Current**: pyproject.toml references `src/` structure
   - **Required**: Update paths for new structure
   - **Impact**: Medium - Affects packaging

### Non-Critical Items

- ✓ README.md is comprehensive and HACS-ready
- ✓ LICENSE is present (MIT)
- ✓ Integration follows HA best practices
- ✓ Comprehensive test coverage
- ✓ Documentation is extensive

## Proposed HACS Structure

```
octopus-ha/
├── README.md                    (✓ Keep as-is)
├── LICENSE                      (✓ Keep as-is) 
├── hacs.json                    (✗ CREATE)
├── info.md                      (✗ CREATE)
├── custom_components/           (⚠ MOVE FROM src/)
│   └── octoha/
│       ├── manifest.json        (✓ Keep as-is)
│       ├── __init__.py          (✓ Keep as-is)
│       ├── config_flow.py       (✓ Keep as-is)
│       ├── [all other files]    (✓ Move as-is)
├── tests/                       (✓ Keep as-is)
├── docs/                        (✓ Keep as-is)
├── pyproject.toml               (⚠ UPDATE paths)
└── .github/                     (✓ Keep as-is)
```

## Migration Risks and Considerations

### Low Risk
- Integration code is complete and tested
- README and documentation are comprehensive
- License is appropriate (MIT)
- No breaking changes to integration functionality

### Medium Risk  
- Build configuration needs updates for new paths
- CI/CD may need adjustment for path changes
- Development workflow changes (imports, test paths)

### Validation Required
- Test suite still passes after migration
- Integration can be imported correctly
- HACS validation passes

## Success Criteria

### Pre-Migration Validation
- [ ] All current tests pass
- [ ] Integration loads correctly in HA
- [ ] Build process works

### Post-Migration Validation
- [ ] Tests pass with new structure
- [ ] Integration installs via HACS
- [ ] hacs.json validates correctly
- [ ] All imports work correctly
- [ ] Build/packaging works with updated paths

### HACS Publication Ready
- [ ] Repository structure matches HACS requirements
- [ ] hacs.json contains correct metadata
- [ ] info.md provides clear description  
- [ ] Integration can be discovered and installed via HACS

## Recommended Next Steps

1. **Create HACS metadata files** (hacs.json, info.md)
2. **Move integration directory** from `src/custom_components/` to `custom_components/`
3. **Update build configuration** (pyproject.toml paths)
4. **Validate migration** with test suite
5. **Test HACS installation** locally
6. **Submit to HACS** community store

## Additional Resources Discovered

- Comprehensive test suite (255+ tests) provides confidence in migration
- Documentation is already HACS-ready in README.md
- Integration follows Home Assistant official patterns  
- Proper versioning and changelog already in place
- GitHub repository structure supports HACS requirements

## File Movement Summary

### Files to Move
- All contents of `src/custom_components/octoha/` → `custom_components/octoha/`

### Files to Create
- `hacs.json` (HACS metadata)
- `info.md` (Short description)

### Files to Update  
- `pyproject.toml` (update build paths)
- Any documentation referencing `src/` paths

### Files to Keep As-Is
- `README.md`
- `LICENSE` 
- `CHANGELOG.md`
- `tests/` directory
- `docs/` directory
- `.github/` directory