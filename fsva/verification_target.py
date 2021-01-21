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
        # Attributes for verification command.
        self.command = "fusesoc"
        self.command_arguments = ["--cores-root", ".", "run", "--no-export", "--target"]
        # Attributes for verification results.
        self.passed = False
        self.number_of_errors = 0
        self.number_of_warnings = 0
        # TODO: add attribute with time for verification

    def _prepare_output_directory(self, outpath):
        core_name = self.core_name.strip(":").replace(":", "-")

        self.outpath = outpath + "/" + core_name + "/" + self.target_name + "/"
        try:
            os.makedirs(self.outpath)
        except FileExistsError:
            pass

    def _prepare_analyze_options(self):
        self.command_arguments.append(self.target_name)
        self.command_arguments.append(self.core_name)

        # Add path for pre analyzed libraries for GHDL.
        #  Right now it is hardcoded to the default GHDL installation path.
        #  If there is a need correct path will be detected automatically.
        if self.eda_tool == "ghdl":
            self.command_arguments.append("--analyze_options")
            self.command_arguments.append(
                "\\-P/usr/local/lib/ghdl/vendors -frelaxed-rules -fpsl"
            )

    def _prepare_run_options(self):
        if self.eda_tool == "ghdl":
            ghdl_psl_report_file = self.outpath + "ghdl_psl_report.json"
            ghdl_vcd_file = self.outpath + "ghdl.ghw"
            self.command_arguments.append("--run_options")
            self.command_arguments.append(
                "\\--psl-report=" + ghdl_psl_report_file + " --wave=" + ghdl_vcd_file
            )

    def _prepare_for_verification(self, outpath):
        self._prepare_output_directory(outpath)
        self._prepare_analyze_options()
        self._prepare_run_options()

    def _verify(self):
        print("Verifying core: " + self.core_name + ", target: " + self.target_name)

        output = subprocess.run(
            [self.command] + self.command_arguments,
            capture_output=True,
            encoding="utf-8",
        )

        if output.returncode == 0:
            self.passed = True

        self.number_of_errors = output.stdout.lower().count("error")
        self.number_of_warnings = output.stdout.lower().count("warn")

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

        print("ERRORS:    " + str(self.number_of_errors))
        print("WARNINGS:  " + str(self.number_of_warnings))
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
