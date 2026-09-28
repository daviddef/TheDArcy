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

def resolve(dist):
    """What to grade when the caller ALSO passed a --dist flag.

    THE ENVIRONMENT BEATS THE FLAG, exactly as it does in the kit. This
    function has to exist because out() wired in as an argparse DEFAULT is
    not enough, and that is a subtler hole than the one this module was
    written to close: a default is consulted only when the flag is ABSENT,
    and site/package.json passes `--dist dist` explicitly. So the tool whose
    own docstring is about this fault went on grading a four-day-old build
    while every other gate read the new one — and reported ok, on the living
    rule, which is the one rule here that is absolute. See own error 45.
    """
    return out() if os.environ.get("ARCHIVE_OUT") else (dist or out())


def note(dist):
    """One line for a tool to print, so a reader knows which build was read."""
    return ("" if not os.environ.get("ARCHIVE_OUT")
            else f"  ..    reading {os.path.relpath(dist, ROOT)} (ARCHIVE_OUT)")


def strict_argv(argv=None):
    """Refuse a flag this gate does not take, instead of ignoring it.

    28 September 2026. A neighbouring session ran

        python3 tools/check_links.py --dist <a fresh build>

    twice, and reported a FAIL both times. check_links.py has no argparse and
    takes no arguments, so `--dist` was silently swallowed and the gate graded
    whatever stale `dist` happened to be on disk while the fresh build sat
    untouched beside it. Two sessions then held two different numbers for the
    same question, and it took a request for the exact command to settle.

    The gate was not wrong and the caller was not careless: the tool ACCEPTED
    an argument and ignored it, which is the worst of the three things it could
    have done. Eight gates here were in that position.

    So they say so now. ARCHIVE_OUT is the way to point any of them at a build,
    and it is the only way, which is also what makes them agree with each other.
    """
    import sys as _sys
    extra = [a for a in (_sys.argv[1:] if argv is None else argv)]
    if not extra:
        return
    name = os.path.basename(_sys.argv[0])
    print(f"  FAIL  {name} takes no arguments, and was given: {' '.join(extra)}")
    print(f"        It would otherwise have IGNORED them and graded "
          f"{name_of()} — which is how a stale build gets read as a fresh one.")
    print(f"        Point it at a build with the environment instead:")
    print(f"            ARCHIVE_OUT=<dir> python3 tools/{name}")
    raise SystemExit(2)


def name_of():
    return name()
