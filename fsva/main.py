import os
import argparse
import subprocess
import pathlib
from datetime import datetime
import zipfile
import shutil
import concurrent.futures
import multiprocessing

from fsva import verification_target


VERSION = "1.2.0"


def parse_cmd_line_args():
    parser = argparse.ArgumentParser(
        prog="fsva",
        description="FuseSoc Verification Automation (fsva) - tool for automating verification process for HDL projects using FuseSoc build tool.",
    )

    # Positional arguments for single core runs and console output
    parser.add_argument(
        "--version", help="Display fsva version.", action="version", version=VERSION
    )
    parser.add_argument("core", nargs="?", help="Core to verify - console output.")
    parser.add_argument(
        "target", nargs="?", help="Verification target to run - console output."
    )

    parser.add_argument(
        "-w",
        "--workpath",
        default=".",
        help="Work path. Path to recursively look for FuseSoc .core files.",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        default="_fsva",
        help="Output directory name. This directory is created in workpath.",
    )
    parser.add_argument(
        "-c",
        "--compress",
        action="store_true",
        help="Automatically compress output directory if all tests pass.",
    )
    parser.add_argument(
        "-n",
        "--numprocesses",
        type=int,
        default=multiprocessing.cpu_count(),
        help="Number of processes allowed to be spawn in parallel. By default value returned from multiprocessing.cpu_count() is used.",
    )

    return parser.parse_args()


def check_fusesoc_installed():
    try:
        out = subprocess.check_output(["fusesoc", "--version"])
        print("Found FuseSoc version: " + out.decode("utf-8"))
    except:
        print("FuseSoc not found!")
        exit(1)


def check_workpath_exists(path):
    if not os.path.exists(path):
        print("Workpath does not exist!")
        exit(1)


def verify_single_core(targets, core, target, outpath):
    """
    Parameters:
    -----------
    targets
        List of verification targets found in all .core files.
    core
        Core name.
    target
        Target name. If target is None, then all verification targets
        for specified core are run.
    outpath
        Output path.
    """
    core_found = False
    core_targets = []
    for t in targets:
        if t.core_name == core:
            core_found = True
            if target is None or t.target_name == target:
                core_targets.append(t)

    if not core_found:
        print("Core: " + core + " not found")
        exit(1)

    if not core_targets:
        print("No verification targets found for core: " + core + ", target: " + target)
        exit(1)

    fail_count = 0
    for t in core_targets:
        t.verify_to_console(outpath)
        if not t.passed:
            fail_count += 1

    return fail_count


def print_summary(file, msg):
    file.write(msg)
    msg = msg.replace("PASSED", "\033[92mPASSED\033[0m")
    msg = msg.replace("FAILED", "\033[91mFAILED\033[0m")
    print(msg, end="")


def summarize(targets, outpath, start_time):
    targets_count = len(targets)
    passed_count = sum(1 for x in targets if x.passed)
    failed_count = targets_count - passed_count
    all_passed = True

    print()

    with open(outpath + "/summary", "w") as f:
        errors_count = 0
        warnings_count = 0

        for target in targets:
            if target.passed:
                print_summary(
                    f, "PASSED: " + target.core_name + " " + target.target_name + "\n"
                )
            else:
                all_passed = False
                print_summary(
                    f, "FAILED: " + target.core_name + " " + target.target_name + "\n"
                )

            if target.errors_count > 0:
                errors_count += target.errors_count
                print_summary(f, "ERRORS " + str(target.errors_count) + "\n")

            if target.warnings_count > 0:
                warnings_count += target.warnings_count
                print_summary(f, "WARNINGS " + str(target.warnings_count) + "\n")

            if not target.passed or target.warnings_count > 0:
                print_summary(f, "DETAILS: " + target.outpath + "\n")

        s = (datetime.now() - start_time).seconds
        hours, remainder = divmod(s, 3600)
        minutes, seconds = divmod(remainder, 60)

        summary = """
SUMMARY:
  TOTAL TIME: {} h {} min {} s
  TARGETS:  {}
  PASSED:   {} ({:.2%})
  FAILED:   {} ({:.2%})
  ERRORS:   {}
  WARNINGS: {}
""".format(
            hours,
            minutes,
            seconds,
            targets_count,
            passed_count,
            passed_count / targets_count,
            failed_count,
            failed_count / targets_count,
            errors_count,
            warnings_count,
        )

        print_summary(f, summary)

    if not all_passed:
        print("At least one verification target failed. Check summary for details.")
        exit(1)


def compress_output_directory(outpath):
    print(outpath)

    dirs_names = outpath.split("/")

    os.chdir(dirs_names[-2])
    zipf = zipfile.ZipFile(dirs_names[-1] + ".zip", "w", zipfile.ZIP_DEFLATED)

    for root, dirs, files in os.walk(outpath):
        for file in files:
            root_dirs = root.split("/")
            idx = root_dirs.index(dirs_names[-1])
            zip_dirs = root_dirs[idx:]
            arcname = "/".join(zip_dirs) + "/" + file
            zipf.write(os.path.join(root, file), arcname)

    zipf.close()
    shutil.rmtree(dirs_names[-1])


def main():
    args = parse_cmd_line_args()

    check_fusesoc_installed()

    check_workpath_exists(args.workpath)
    workpath = os.path.abspath(args.workpath)
    os.chdir(workpath)

    start_time = datetime.now()

    core_files = []
    for file in pathlib.Path(workpath).glob("**/*.core"):
        core_files.append(file)

    if not core_files:
        print("No .core files found under the workpath")
        exit(1)

    # Collect verification targets from .core files.
    targets = []
    for file in core_files:
        targets += verification_target.from_file(file)

    if not targets:
        print("No verification targets found in .core files")
        exit(1)

    outpath = workpath + "/" + args.outdir + "/"

    if args.core:
        outpath += "tmp"
        if verify_single_core(targets, args.core, args.target, outpath) > 0:
            exit(1)
        else:
            exit(0)

    outpath += datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if int(args.numprocesses) < 1:
        workers = 1
    else:
        workers = int(args.numprocesses)

    print(f"Running {len(targets)} verification targets with {workers} workers.\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        executor.map(lambda t: t.verify_to_file(outpath), targets)

    summarize(targets, outpath, start_time)

    if args.compress:
        compress_output_directory(outpath)


if __name__ == "__main__":
    main()
