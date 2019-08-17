use std::process;

use clap::{App, Arg};

fn main() {
    let config = App::new("FuseSoc Verification Automation")
        .about(
            "Tool for automating verification process for HDL projects using FuseSoc build tool."
        )
        .version("0.1.0")
        .author("Michał Kruszewski mkru@protonmail.com")
        .arg(
            Arg::with_name("workpath")
                .long("workpath")
                .short("w")
                .help("Work path. Path to recursively look for FuseSoc .core files.")
                .takes_value(true)
                .default_value(".")
                .validator(workpath_validator)
        )
        .arg(
            Arg::with_name("outdir")
                .long("outdir")
                .short("o")
                .help("Output directory name. This directory is created in workpath.")
                .takes_value(true)
                .default_value("_fsva")
        )
        .arg(
            Arg::with_name("numprocesses")
                .long("numprocesses")
                .short("n")
                .help("Number of processes allowed to be spawn in parallel.")
                .takes_value(true)
                .default_value("1")
                .validator(numprocesses_validator)
        )
        .arg(
            Arg::with_name("compress")
                .long("compress")
                .short("c")
                .help("Automatically compress output directory if all tests pass.")
        )
        .get_matches();

    if config.is_present("compress") {
        println!("Compression of the output directory is not yet supported.");
        process::exit(1);
    }

    if config.value_of("numprocesses").unwrap().parse::<u32>().unwrap() > 1 {
        println!("Parallel verification is not yet supported.");
        process::exit(1);
    }

    let output = process::Command::new("fusesoc")
        .arg("--version")
        .output()
        .expect("Failed to launch fusesoc, is it installed?");
    print!("Found fusesoc version {}\n", String::from_utf8(output.stdout).unwrap());

    if let Err(e) = fsva::run(config) {
        eprintln!("\nApplication error: {}", e);

        process::exit(1);
    }
}

fn workpath_validator(val: String) -> Result<(), String> {
    let workpath = fsva::string_to_path(val);

    if workpath.exists() {
        return Ok(())
    }

    Err(format!("{:?} workpath does not exist.", workpath))
}

fn numprocesses_validator(val: String) -> Result<(), String> {
    match val.parse::<u32>() {
        Ok(_) => Ok(()),
        Err(e) => Err(e.to_string()),
    }
}
