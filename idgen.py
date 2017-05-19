
import argparse

import exprparse
import generator


LOG_DEBUG = False


def parse_args():
    parser = argparse.ArgumentParser(
            description="Generator of identifier"
            )
    parser.add_argument("-c", "--count", type=int, help="Number of identifier generated")
    parser.add_argument("pattern", type=str, help="Identifier format")
    return parser.parse_args()


if __name__ == "__main__":
    import os
    LOG_DEBUG = bool(os.getenv("LOG_DEBUG", LOG_DEBUG))

    args = parse_args()
    parser = exprparse.Source(args.pattern)
    fields = parser.parse_and_build()
    limit = int(args.count if args.count else 20)
    for id_ in generator.IdentifierGenerator(fields, limit):
        print(id_)

