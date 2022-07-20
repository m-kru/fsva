import yaml
import os
import subprocess


class VerificationTarget:
    def __init__(self):
        self.core_file = None
        self.core_name = None
        self.target_name = None
        self.eda_tool = None
        self.outpath = (None,)
        # Verification command attributes.
        self.cmd = "fusesoc"
        self.cmd_args = ["--cores-root", ".", "run", "--no-export", "--target"]
        # Verification result attributes.
        self.passed = False
        self.errors_count = 0
        self.warnings_count = 0
        # TODO: add attribute with time for verification

    def _prepare_output_directory(self, outpath):
        core_name = self.core_name.strip(":").replace(":", "-")

        self.outpath = outpath + "/" + core_name + "/" + self.target_name + "/"
        try:
            os.makedirs(self.outpath)
        except FileExistsError:
            pass

    def _prepare_analyze_options(self):
        self.cmd_args.append(self.target_name)
        self.cmd_args.append(self.core_name)

        # Add path for pre analyzed libraries for GHDL.
        #  Right now it is hardcoded to the default GHDL installation path.
        #  If there is a need correct path will be detected automatically.
        if self.eda_tool == "ghdl":
            self.cmd_args.append("--analyze_options")
            self.cmd_args.append(
                "\\-P/usr/local/lib/ghdl/vendors -frelaxed-rules -fpsl"
            )

    def _prepare_run_options(self):
        if self.eda_tool == "ghdl":
            ghdl_psl_report_file = self.outpath + "ghdl_psl_report.json"
            ghdl_vcd_file = self.outpath + "ghdl.ghw"
            self.cmd_args.append("--run_options")
            self.cmd_args.append(
                "\\--psl-report=" + ghdl_psl_report_file + " --wave=" + ghdl_vcd_file
            )

    def _prepare_for_verification(self, outpath):
        self._prepare_output_directory(outpath)
        self._prepare_analyze_options()
        self._prepare_run_options()

    def _verify(self):
        print(self.core_name + " " + self.target_name)

        output = subprocess.run(
            [self.cmd] + self.cmd_args, capture_output=True, encoding="utf-8"
        )

        if output.returncode == 0:
            self.passed = True

        self.errors_count = output.stdout.lower().count("error")
        self.warnings_count = output.stdout.lower().count("warn")

        return output

    def verify_to_file(self, outpath):
        self._prepare_for_verification(outpath)

        output = self._verify()

        with open(self.outpath + "output.txt", "w") as f:
            f.write("************************************************************\n")
            f.write("*****                      STDERR                      *****\n")
            f.write("************************************************************\n\n")
            f.write(output.stderr)

            f.write("\n\n")
            f.write("************************************************************\n")
            f.write("*****                      STDOUT                      *****\n")
            f.write("************************************************************\n\n")
            f.write(output.stdout)

    def verify_to_console(self, outpath):
        self._prepare_for_verification(outpath)

        output = self._verify()

        print("")
        print("************************************************************")
        print("*****                      STDERR                      *****")
        print("************************************************************\n")
        print(output.stderr)

        print("")
        print("************************************************************")
        print("*****                      STDOUT                      *****")
        print("************************************************************\n")
        print(output.stdout)

        print("core: " + self.core_name + ", target: " + self.target_name)

        if self.passed:
            print("\033[92m" + "PASSED" + "\033[0m")
        else:
            print("\033[91m" + "FAILED" + "\033[0m")

        print("ERRORS:    " + str(self.errors_count))
        print("WARNINGS:  " + str(self.warnings_count))
        print("")


def from_file(file):
    """
    Returns verification targets from single FuseSoc .core file.

    :param file: .core file
    :return: list with verification targets
    """
    with open(file) as f:
        try:
            yaml_dict = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)

    if "targets" not in yaml_dict:
        return []

    verification_targets = []
    for target in yaml_dict["targets"]:
        if target == "tb" or target.startswith("tb_") or target.endswith("_tb"):
            ver_target = VerificationTarget()
            ver_target.core_file = f.name
            ver_target.core_name = yaml_dict["name"]
            ver_target.target_name = target
            ver_target.eda_tool = yaml_dict["targets"][target]["default_tool"]
            verification_targets.append(ver_target)

    return verification_targets
