
import argparse

import fix_import
import parser
import ast
import state_machine as sm


def parse_args():
    pargs = argparse.ArgumentParser(description="Manual parse expression")
    pargs.add_argument("expr", help="expression to parse")
    return pargs.parse_args()


def print_source(psm: sm.PSM):
    print("Source:", psm.source.curr, "   State:", psm.state)


def print_state_is_done(psm: sm.PSM):
    if psm.source.done:
        print("Done with state:", psm.state)


if __name__ == "__main__":
    args = parse_args()
    expr_ast = parser.parse(args.expr,
                            pre_action=print_source,
                            post_action=print_state_is_done)
    ast.print(expr_ast)
