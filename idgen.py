
import argparse

import exprparse
import generator



def parse_args():
    parser = argparse.ArgumentParser(
            description="Generator of identifier"
            )
    parser.add_argument("-c", "--count", type=int, help="Number of identifier generated")
    parser.add_argument("pattern", type=str, help="Identifier format")
    return parser.parse_args()


if __name__ == "__main__":
    import os.path
    import logging
    import logging.config
    if os.path.exists("log_conf.ini"):
        logging.config.fileConfig("log_conf.ini")

    args = parse_args()
    parser = exprparse.Source(args.pattern)
    fields = parser.parse_and_build()
    limit = int(args.count if args.count else 20)
    for id_ in generator.IdentifierGenerator(fields, limit):
        print(id_)

