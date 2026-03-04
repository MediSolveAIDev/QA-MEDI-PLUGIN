"""진입점: python -m orchestrator"""

import sys
import asyncio

from orchestrator.cli import parse_args
from orchestrator.engine import PipelineEngine


def main():
    args = parse_args(sys.argv[1:])
    engine = PipelineEngine(args)

    if args.parallel_projects and len(args.parallel_projects) > 1:
        asyncio.run(engine.run_parallel(args.parallel_projects))
    else:
        engine.run()


if __name__ == "__main__":
    main()
