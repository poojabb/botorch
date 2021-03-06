#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile
import time
from pathlib import Path
from subprocess import CalledProcessError

import nbformat
from nbconvert import PythonExporter


IGNORE = {
    # some nbs take quite a while, don't run by default
    "closed_loop_botorch_only.ipynb",
    "meta_learning_with_rgpe.ipynb",
    "multi_objective_bo.ipynb",
    "preference_bo.ipynb",
    # some others may require setting paths to local data
    "vae_mnist.ipynb",
}


def parse_ipynb(file: Path) -> str:
    with open(file, "r") as nb_file:
        nb_str = nb_file.read()
    nb = nbformat.reads(nb_str, nbformat.NO_CONVERT)
    exporter = PythonExporter()
    script, _ = exporter.from_notebook_node(nb)
    return script


def run_script(script: str) -> None:
    # need to keep the file around & close it so subprocess does not run into I/O issues
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf_name = tf.name
        with open(tf_name, "w") as tmp_script:
            tmp_script.write(script)
    run_out = subprocess.run(["ipython", tf_name], capture_output=True, text=True)
    os.remove(tf_name)
    return run_out


def run_tutorial(tutorial: Path) -> None:
    script = parse_ipynb(tutorial)
    tic = time.time()
    print(f"Running tutorial {tutorial.name}.")
    run_out = run_script(script)
    try:
        run_out.check_returncode()
    except CalledProcessError:
        raise RuntimeError(
            "\n".join(
                [
                    f"Encountered error running tutorial {tutorial.name}:",
                    "stdout:",
                    run_out.stdout,
                    "stderr:",
                    run_out.stderr,
                ]
            )
        )
    runtime = time.time() - tic
    print(f"Running tutorial {tutorial.name} took {runtime:.2f} seconds.")


def run_tutorials(repo_dir: str) -> None:
    tutorial_dir = Path(repo_dir).joinpath("tutorials")
    for tutorial in tutorial_dir.iterdir():
        if not tutorial.is_file or tutorial.suffix != ".ipynb":
            continue
        if tutorial.name in IGNORE:
            print(f"Ignoring tutorial {tutorial.name}.")
            continue
        run_tutorial(tutorial)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the tutorials.")
    parser.add_argument(
        "-p", "--path", metavar="path", required=True, help="botorch repo directory."
    )
    args = parser.parse_args()
    run_tutorials(args.path)
