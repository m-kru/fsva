use std::env::{current_dir, set_current_dir};
use std::error::Error;
use std::fs;
use std::io;
use std::io::prelude::*;
use std::path::PathBuf;
use std::process;
use std::time;

use clap::ArgMatches;
use serde_yaml as sy;
use chrono::prelude::Utc;

pub fn run(config: ArgMatches) -> Result<(), Box<dyn Error>> {
    let now = time::Instant::now();
    let workpath = string_to_path(config.value_of("workpath").unwrap().to_string());
    set_current_dir(&workpath)?;

    let core_files = find_core_files(&workpath)?;

    if core_files.is_empty() {
        return Err(format!("No .core files found under the workpath: {:?}.", workpath).into());
    }

    let mut verification_targets = vec![];
    for file in core_files {
        verification_targets.append(&mut VerificationTarget::new(&file)?);
    }

    if verification_targets.is_empty() {
        return Err(format!("No verification targets found.").into());
    }

    let date_utc = Utc::now()
                    .format("%Y-%m-%d_%H:%M:%S")
                    .to_string();

    let outpath: PathBuf = workpath.join(config.value_of("outdir").unwrap().to_string())
                    .join(date_utc);
    fs::create_dir_all(&outpath)?;

    for target in &mut verification_targets {
        target.prepare_for_verification(&outpath);
    }

    for target in &mut verification_targets {
        target.verify()?;
    }

    summarize(verification_targets, now)?;

    Ok(())
}

fn summarize(verification_targets: Vec<VerificationTarget>,
             time_measure: time::Instant) -> Result<(), &'static str> {
    let num_targets = verification_targets.len();
    let num_passed = verification_targets.iter()
                            .filter(|x| x.passed)
                            .count();
    let num_failed = num_targets - num_passed;

    let mut all_passed = true;
    let mut num_warnings = 0;

    for target in verification_targets {
        if !target.passed {
            all_passed = false;
            println!("\nFAILED: core: {}, target: {}", target.core_name, target.target_name);
        }

        if target.number_of_warnings > 0 {
            num_warnings += target.number_of_warnings;

            println!("Warnings found for core: {}, target: {}", target.core_name, target.target_name);
        }

        if !target.passed || target.number_of_warnings > 0 {
            println!("For more details check file: {:?}\n", target.output_file);
        }
    }


    let summary = format!("\nVERIFICATION SUMMARY:
  Total verification time: {}
  TARGETS:  {}
  PASSED:   {} ({:.2}%)
  FAILED:   {} ({:.2}%)
  WARNINGS: {}\n",
        ms_to_min_s_ms(time_measure.elapsed().as_millis()),
        num_targets,
        num_passed,
        num_passed as f32 / num_targets as f32 * 100.0,
        num_failed,
        num_failed as f32 / num_targets as f32 * 100.0,
        num_warnings);

    println!("{}", summary);

    if !all_passed {
        return Err("At least one verification target failed. Check summary for details.");
    }

    Ok(())
}

fn ms_to_min_s_ms(ms_in: u128) -> String {
    let ms = ms_in % 1000;
    let s = (ms_in / 1000) % 60;
    let min = ms_in / 1000 / 60;

    format!("{} min {} s {} ms", min, s, ms).to_string()
}

#[derive(Clone, Debug)]
//#[derive(Debug)]
struct VerificationTarget {
    core_file: PathBuf,
    core_name: String,
    target_name: String,
    eda_tool: String,
    output_file: PathBuf,
    // Attributes for verification command.
    command: String,
    command_arguments: Vec<String>,
    // Attributes for verification results.
    passed: bool,
    number_of_warnings: u32,
    // TODO: add attribute with time for verification
}

impl Default for VerificationTarget {
    fn default() -> VerificationTarget {
        VerificationTarget {
            core_file: PathBuf::new(),
            core_name: String::new(),
            target_name: String::new(),
            eda_tool: String::new(),
            output_file: PathBuf::new(),
            command: String::from("fusesoc"),
            command_arguments: vec![String::from("--cores-root"),
                                    String::from("."),
                                    String::from("run"),
                                    String::from("--target")],
            passed: false,
            number_of_warnings: 0,
        }
    }
}

impl VerificationTarget {
    // Return Vec as single .core file can contain multiple verification targets.
    fn new(file: &PathBuf) -> Result<Vec<VerificationTarget>, Box<dyn Error>> {
        let mut ver_targets = vec![];

        let f = fs::File::open(file)?;

        let yaml: sy::Value = sy::from_reader(f)?;

        let core_name;
        match yaml.get("name").unwrap() {
            sy::Value::String(s) => core_name = s,
            _ => return Err(format!("core name must be string, file: {:?}", file).into()),
        }

        if let sy::Value::Mapping(m) = yaml.get("targets").unwrap() {
            for target in m {

                if let sy::Value::String(target_name) = target.0 {
                    if target_name.starts_with("tb_") || target_name.ends_with("_tb") {
                        let tool = target.1.get("default_tool");
                        let mut eda_tool = String::from("");
                        if tool.is_some() {
                            if let sy::Value::String(s) = tool.unwrap() {
                                eda_tool = s.to_string();
                            }
                        }

                        let ver_target = VerificationTarget {
                            core_file: file.to_path_buf(),
                            core_name: core_name.clone(),
                            target_name: target_name.clone(),
                            eda_tool: eda_tool.clone(),
                            ..VerificationTarget::default()};
                        ver_targets.push(ver_target);
                    }
                }
            }
        }

        Ok(ver_targets)
    }

    fn prepare_for_verification(&mut self, outpath: &PathBuf) {
        let file_name = self.core_name.trim_start_matches(':')
                            .replace(":", "-") + "_" + &self.target_name;
        self.output_file = outpath.join(file_name);

        self.command_arguments.push(self.target_name.clone());
        self.command_arguments.push(self.core_name.clone());
    }

        fn verify(&mut self) -> io::Result<()> {
            println!("Verifying core: {}, target: {}", self.core_name, self.target_name);
            let output = process::Command::new(self.command.clone())
                .args(self.command_arguments.clone())
                .output()?;

            if output.status.success() {
                self.passed = true;
            }

            let mut file = fs::File::create(self.output_file.clone())?;
            file.write_all(b"***** STANDARD ERROR *****\n\n")?;
            file.write_all(&output.stderr)?;

            file.write_all(b"\n***** STANDARD OUTPUT *****\n\n")?;
            file.write_all(&output.stdout)?;

            Ok(())
        }
}

pub fn string_to_path(val: String) -> PathBuf {
    let mut path = PathBuf::from(val);

    if !path.is_absolute() {
        path = current_dir().unwrap().join(path);
    }

    path
}

fn find_core_files(dir: &PathBuf) -> io::Result<Vec<PathBuf>> {
    let mut core_files = vec![];

    if dir.is_dir() {
        for entry in fs::read_dir(dir)? {
            let entry = entry?;
            let path = entry.path();
            if path.is_dir() {
                core_files.append(&mut find_core_files(&path)?);
            } else {
                match path.extension() {
                    Some(e) => {
                        if e == "core" {
                            core_files.push(path);
                        }
                    }
                    _ => (),
                }
            }
        }
    }

    Ok(core_files)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn string_to_path_absolute() {
        let s = String::from("/tmp/abc/def");
        let p = PathBuf::from("/tmp/abc/def");

        assert_eq!(p, string_to_path(s));
    }

    #[test]
    fn test_ms_to_min_s_ms() {
        assert_eq!("0 min 0 s 7 ms", ms_to_min_s_ms(7));
        assert_eq!("0 min 1 s 48 ms", ms_to_min_s_ms(1048));
        assert_eq!("17 min 5 s 13 ms", ms_to_min_s_ms(1025013));
    }
}
