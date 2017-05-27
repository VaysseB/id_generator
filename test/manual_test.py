
import argparse

import fix_import
import parser
import ast
import state_machine as sm


def parse_args():
    pargs = argparse.ArgumentParser(description="Manual parse expression")
    pargs.add_argument("--quiet", help="silent parsing", action="store_true")
    pargs.add_argument("action", help="action to make after parsing",
                      default="print", choices=("print", "visit"),
                      nargs="?")
    pargs.add_argument("expr", help="expression to parse")
    return pargs.parse_args()


def print_source(psm: sm.PSM):
    print("Source:", psm.source.curr, "   State:", psm.state)


def print_state_is_done(psm: sm.PSM):
    if psm.source.done:
        print("Done with state:", psm.state)


if __name__ == "__main__":
    args = parse_args()

    if args.quiet:
        expr_ast = parser.parse(args.expr)
    else:
        expr_ast = parser.parse(args.expr,
                                pre_action=print_source,
                                post_action=print_state_is_done)

    if args.action == "print":
        ast.print(expr_ast)
    elif args.action == "visit":
        class DebugVisitor(object):
            def __getattr__(self, name):
                keyword = "visit_"
                ntype = name[len(keyword):]
                if name.startswith(keyword):
                    return lambda x,n=ntype: print("Visit " + n + ":", x)
                return super(DebugVisitor, self).__getattribute__(name)

        ast.visit(expr_ast, DebugVisitor())
