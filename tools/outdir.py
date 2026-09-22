#!/usr/bin/env python3
"""Which build is this tool grading? One answer, for every tool in this archive.

On 22 September the estate's harmonisation session found that `ARCHIVE_OUT` —
the variable an operator sets to say «read the build I just made» — was honoured
by NO tool in the shared kit. Four took a `--dist` flag, every archive's
package.json passed `--dist dist` on the command line, and the variable was read
by nothing and overridden by everything. Runs made all afternoon to verify that
living people had been removed from a page reported on whatever the shared `dist`
happened to hold. They passed. They were not evidence.

The kit honours it now, and THE ENVIRONMENT BEATS THE FLAG there — deliberately,
because the flag is the repository's default and the variable is an operator
speaking. This archive's own tools hardcoded `site/dist` and honoured nothing,
which after that fix is the worse state of the two: the kit's gates would grade
one directory and these would grade another, and a split verdict over one build
is harder to catch than a wrong one.

So they all ask here.

    ARCHIVE_OUT=dist-verify ./build.sh    # every gate reads dist-verify
    ./build.sh                            # every gate reads site/dist
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def out(default=None):
    """The directory to grade. ARCHIVE_OUT wins; it is the operator speaking."""
    env = os.environ.get("ARCHIVE_OUT")
    if env:
        return env if os.path.isabs(env) else os.path.join(ROOT, "site", env)
    return default or os.path.join(ROOT, "site", "dist")


def name():
    """What to call it in a message, so a reader knows which build was read."""
    return os.path.relpath(out(), ROOT)
