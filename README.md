# fsva - FuseSoc Verification Automation

## Status
The project is considered as finished.
Only following changes will be accepted:
- new tools support,
- bug fixes,
- minor improvements not breaking backward compatibility.

## Introduction

FuseSoc Verification Automation (fsva) is a tool that aims to automate the verification process of libraries and HDL design projects managed with [FuseSoc](https://github.com/olofk/fusesoc) build tool/system.

Fsva in no way duplicates or replaces functionalities provided by the FuseSoc.
Colloquially speaking, fsva is a wrapper for FuseSoc, automating the verification process.
It simply detects and runs verification targets, and parses verification results.

### Why?
The major goal is to easily integrate project/libraries described in FuseSoc into Continuous Integration workflow.
FuseSoc is more than good for building and running single targets, however if you want to run multiple verificaiton targets it keeps rebuilding verification frameworks.
This particular operation is redundant and time consuming.
Fsva assumes that verification frameworks (such as [UVVM](https://github.com/UVVM/UVVM) or [OSVVM](https://github.com/OSVVM/OSVVM)) are already pre-compiled (pre-analyzed) for simulation engines.
What is more, fsva extends FuseSoc by parsing verification results.

## How it works
Fsva scans recursively for `.core` files and fetches all targets with name `tb` or name starting with `tb_` or ending with `_tb`.
Then it runs these targets calling FuseSoc run command and captures stdout and stderr.
By default verification targets are run in parallel.
The default number of concurrent processes equals `multiprocessing.cpu_count()`.
All verification results, as well as verification summary, are saved as separate files in a directory, which name reflects the UTC time of a verification process startup.
Under the UTC time directory, the cores directories are located.
Each core directory contains directories with results for particular verification targets.
Example `_fsva` output directory structure:
```
_fsva/
└── 2020-07-15_16-31-47
    ├── div_by_3
    │   └── div_by_3_tb
    │       └── output.txt
    ├── gbt_link_checker
    │   ├── checker_tb
    │   │   └── output.txt
    │   ├── generator_1_tb
    │   │   └── output.txt
    │   └── generator_2_tb
    │       └── output.txt
    ├── psl
    │   └── tb_0
    │       ├── ghdl.ghw
    │       ├── ghdl_psl_report.json
    │       └── output.txt
    └── summary
```

Fsva does not, and never will, perform any advanced results parsing such as scoreboard analysis or UVM coverage analysis.
Fsva does one thing, and tries to do it well.

If one needs advanced results parsing (for example in case of metric driven verification), then the proper parser needs to be run after fsva has finished.
To make the discovery of reuslts for such test benches easier, one can use special form of prefix or suffix indicating verification framework, infrastructure etc.
For instance, for UVVM one can use  `tb_uvvm_` / `_uvvm_tb`, respectively for OSVVM one can use `tb_osvvm_` / `_osvvm_tb`.

If FuseSoc supports formal verification targets in the future, they will be fetched based on `fv_` prefix or `_fv` suffix.

## Installation
Latest stable version of fsva can be installed from [PyPI](https://pypi.org/project/fsva/):
`pip install --user fsva`.

Alternatively, you can clone this repository and run `python setup.py install --user`.
## Usage

### Verify project
Execute `fsva` in project root directory to run all verification targets.

<p align="center"><img src="/img/project.gif?raw=true"/></p>

### Verify single core or target
You can also run all verification targets for single core:
`fsva core_name`
or run specific verification target for specific core
`fsva core_name target_name`.
When verifying single core or target, the output is printed on the console.
Extra files, such as waveform, PSL reports etc. are placed under `_fsva/tmp/{core}/{target}/` path.

<p align="center"><img src="/img/single_target.gif?raw=true"/></p>

## Note!
If you use it with UVVM you may need to fix status that is returned when UVVM test bench fails: [Integrating UVVM with Continuous Integration - problem with simulators exit status](https://github.com/UVVM/UVVM/issues/82).
