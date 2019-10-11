import yaml
import os
import subprocess


class VerificationTarget:
    def __init__(self):
        self.core_file = None
        self.core_name = None
        self.target_name = None
        self.eda_tool = None
        self.output_file = None,
        # Attributes for verification command.
        self.command = 'fusesoc'
        self.command_arguments = ['--cores-root', '.', 'run', '--target']
        # Attributes for verification results.
        self.passed = False
        self.number_of_errors = 0
        self.number_of_warnings = 0
        # TODO: add attribute with time for verification

    def _prepare_for_verification(self, outpath):
        self.core_name = self.core_name.strip(':').replace(':', '-')

        try:
            os.mkdir(outpath + '/' + self.core_name)
        except FileExistsError:
            pass

        self.output_file = outpath + '/' + self.core_name + '/' + self.target_name

        self.command_arguments.append(self.target_name)
        self.command_arguments.append(self.core_name)

        # Add path for pre analyzed libraries for GHDL.
        #  Right now it is hardcoded to the default GHDL installation path.
        #  If there is a need correct path will be detected automatically.
        if self.eda_tool == "ghdl":
            self.command_arguments.append('--analyze_options')
            self.command_arguments.append("\\-P/usr/local/lib/ghdl/vendors -frelaxed-rules -fpsl")

            ghdl_psl_report_file = self.output_file + "_ghdl_psl_report.json"
            self.command_arguments.append('--run_options')
            self.command_arguments.append("\\--psl-report=" + ghdl_psl_report_file)

    def verify(self, outpath):
        self._prepare_for_verification(outpath)

        print("Verifying core: " + self.core_name + ", target: " + self.target_name)

        output = subprocess.run([self.command] + self.command_arguments, capture_output=True, encoding='utf-8')

        if output.returncode == 0:
            self.passed = True

        with open(self.output_file, 'w') as f:
            f.write("***** STDERR *****\n\n")
            f.write(output.stderr)

            f.write("\n***** STDOUT *****\n\n")
            f.write(output.stdout)

        self.number_of_errors = output.stdout.lower().count('error')
        self.number_of_warnings = output.stdout.lower().count('warn')


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

    verification_targets = []
    for target in yaml_dict['targets']:
        if target.startswith('tb_') or target.endswith('_tb'):
            ver_target = VerificationTarget()
            ver_target.core_file = f.name
            ver_target.core_name = yaml_dict['name']
            ver_target.target_name = target
            ver_target.eda_tool = yaml_dict['targets'][target]['default_tool']
            verification_targets.append(ver_target)

    return verification_targets
