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
