# fsva - FuseSoc Verification Automation

## Introduction

FuseSoc Verification Automation (fsva) is a tool that aims to automate
the verification process of libraries and HDL design projects managed
with [FuseSoc](https://github.com/olofk/fusesoc) build tool/system.

fsva in no way duplicates or replaces functionalities provided by the FuseSoc.
Ccolloquially speaking, fsva is a wrapper for FuseSoc automating
the verification process.

### Why?
Why not?

## How it works
fsva scans recursively for `.core` files and fetches all targets starting
with `tb_` or ending with `_tb`. Then it runs these targets calling FuseSoc
run command and captures stdout and stderr. All verification results,
as well as verification summary, are saved as separate files in a directory,
which name reflects the UTC time of a verification process startup.

If any extra parsing of the verification results is needed in the future,
it will be based on prefix or suffix indicating verification
framework/infrastructure. For example, for UVVM it will be `tb_uvvm_` / `_uvvm_tb`,
respectively for [OSVVM](https://github.com/OSVVM/OSVVM)
it will be `tb_osvvm_` / `_osvvm_tb`.

If FuseSoc supports formal verification targets in the future, they will be
fetched based on `fv_` prefix or `_fv` suffix.

## Usage
Clone the repository and build with `cargo build --release`.
If you want (you probably want) install output target in visible PATH.

### Example
<p align="center"><img src="/img/demo.gif?raw=true"/></p>
