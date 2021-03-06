#!/usr/bin/env python

import argparse
import inspect
import os
import sys
from pathlib import Path
from src import work

HELP = """
Store by Preston Hunt <me@prestonhunt.com>
https://github.com/presto8/store

An experimental chunk-based backup program. This is a proof-of-concept
implementation to explore concepts which may not be addressed fully in
currently available backup programs.
"""


def parse_args(argv):
    parser = argparse.ArgumentParser(description=HELP, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--storedir', default=os.environ.get('STORE_DIR'), help='location of Store config files')
    parser.add_argument('--verbose', default=False, action='store_true', help='show more detailed messages')
    parser.add_argument('--debug', action='store_true')

    commands = []
    subparsers = parser.add_subparsers(dest='command')

    def add_command(name, *args, **kwargs):
        commands.append(name)
        return subparsers.add_parser(name, *args, **kwargs)

    # 'store' or 'store add'
    x = add_command('add', help='backup pathspec (recursively descend dirs)')
    x.add_argument('pathspec', nargs='+', default=('.',), help="paths to process")
    x.add_argument('--dry-run', '-n', action='store_true', help='do not backup, preview what would happen only')

    # 'store init'
    x = add_command('init', help='initialize a Store')

    # 'store info'
    x = add_command('info', help='show information and statistics for this Store')

    # check for default command
    if argv and argv[0] not in commands:
        argv.insert(0, "add")

    args, unknown_args = parser.parse_known_args(argv)

    if not args and unknown_args:  # default subcommand is 'add'
        args.command = 'add'

    args.unknown_args = unknown_args

    if args.command is None:
        parser.print_help()
        raise SystemExit(1)

    return args


def cli_mapper(args):
    func = getattr(work, args.command.replace("-", "_"))
    sig = inspect.signature(func)
    func_args = sig.parameters.keys()
    missing_args = [arg for arg in func_args if arg not in arg]
    if missing_args:
        raise Fail(f"missing arguments for {func}: {missing_args}")  # pragma: no cover
    pass_args = {k: v for k, v in args.__dict__.items() if k in func_args}
    if 'pathspec' in pass_args.keys():
        pass_args['pathspec'] = [Path(path) for path in pass_args['pathspec']]
    return func(**pass_args)


def main(argv):
    args = parse_args(argv)
    args.work = work.Work(configdir=args.storedir)
    cli_mapper(args)


class Fail(Exception):
    pass


def entrypoint():  # pragma: no cover
    try:
        main(sys.argv[1:])
    except Fail as f:
        print(*f.args, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Ctrl+C")
