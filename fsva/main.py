import os
import argparse
import subprocess
import pathlib
from datetime import datetime
import zipfile
import shutil

from fsva import verification_target


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(
        prog="FuseSoc Verification Automation",
        description="Tool for automating verification process for HDL projects using FuseSoc build tool"
    )

    parser.add_argument('-w', '--workpath', default='.',
                        help="Work path. Path to recursively look for FuseSoc .core files")
    parser.add_argument('-o', '--outdir', default='_fsva',
                        help="Output directory name. This directory is created in workpath")
    parser.add_argument('-c', '--compress', action='store_true',
                        help="Automatically compress output directory if all tests pass")
    parser.add_argument('-n', '--numprocesses', default=1,
                        help="Number of processes allowed to be spawn in parallel.")

    return parser.parse_args()


def check_fusesoc_installed():
    try:
        out = subprocess.check_output(['fusesoc', '--version'])
        print("Found FuseSoc version: " + out.decode('utf-8'))
    except:
        print("FuseSoc not found!")
        exit(1)


def check_workpath_exists(path):
    if not os.path.exists(path):
        print("Workpath does not exist!")
        exit(1)


def print_summary(file, msg):
    print(msg, end='')
    file.write(msg)


def summarize(verification_targets, outpath, start_time):
    num_targets = len(verification_targets)
    num_passed = sum(1 for x in verification_targets if x.passed)
    num_failed = num_targets - num_passed
    all_passed = True

    with open(outpath + '/summary', 'w') as f:
        num_errors = 0
        num_warnings = 0

        for target in verification_targets:
            if target.passed:
                print_summary(f, "PASSED: core: " + target.core_name + ", target: " + target.target_name + "\n")
            else:
                all_passed = False
                print_summary(f, "FAILED: core: " + target.core_name + ", target: " + target.target_name + "\n")

            if target.number_of_errors > 0:
                num_errors += target.number_of_errors

                print_summary(f, "ERRORS (" + str(target.number_of_errors) + "): core: " + target.core_name + ", target: " + target.target_name + "\n")

            if target.number_of_warnings > 0:
                num_warnings += target.number_of_warnings

                print_summary(f, "WARNINGS (" + str(target.number_of_warnings) + "): core: " + target.core_name + ", target: " + target.target_name + "}\n")

            if not target.passed or target.number_of_warnings > 0:
                print_summary(f, "For more details check file:" + target.output_file + "\n")

            print_summary(f, "\n")

        s = (datetime.now() - start_time).seconds
        hours, remainder = divmod(s, 3600)
        minutes, seconds = divmod(remainder, 60)

        summary = """
VERIFICATION SUMMARY:
  Total verification time: {} h {} min {} s
  TARGETS:  {}
  PASSED:   {} ({:.2%})
  FAILED:   {} ({:.2%})
  ERRORS:   {}
  WARNINGS: {}\n
""".format(hours, minutes, seconds,
           num_targets,
           num_passed, num_passed/num_targets,
           num_failed, num_failed/num_targets,
           num_errors,
           num_warnings)

        print_summary(f, summary)

    if not all_passed:
        print("At least one verification target failed. Check summary for details.")
        exit(1)


def compress_output_directory(outpath):
    print(outpath)

    dirs_names = outpath.split('/')

    os.chdir(dirs_names[-2])
    zipf = zipfile.ZipFile(dirs_names[-1] + '.zip', 'w', zipfile.ZIP_DEFLATED)

    for root, dirs, files in os.walk(outpath):
        for file in files:
            root_dirs = root.split('/')
            idx = root_dirs.index(dirs_names[-1])
            zip_dirs = root_dirs[idx:]
            arcname = '/'.join(zip_dirs) + '/' + file
            zipf.write(os.path.join(root, file), arcname)

    zipf.close()
    shutil.rmtree(dirs_names[-1])


if __name__ == '__main__':
    cmd_line_args = parse_command_line_arguments()

    if int(cmd_line_args.numprocesses) > 1:
        print("Parallel verification is not yet supported")
        exit(1)

    check_fusesoc_installed()

    check_workpath_exists(cmd_line_args.workpath)
    workpath = os.path.abspath(cmd_line_args.workpath)
    os.chdir(workpath)

    start_time = datetime.now()

    core_files = []
    for file in pathlib.Path(workpath).glob('**/*.core'):
        core_files.append(file)

    if not core_files:
        print("No .core files found under the workpath")
        exit(1)

    verification_targets = []
    for file in core_files:
        verification_targets += verification_target.from_file(file)

    outpath = workpath + '/' + cmd_line_args.outdir + '/' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    os.makedirs(outpath)

    for target in verification_targets:
        target.verify(outpath)

    summarize(verification_targets, outpath, start_time)

    if cmd_line_args.compress:
        compress_output_directory(outpath)
