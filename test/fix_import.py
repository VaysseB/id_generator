
import os, sys

folder = os.path.dirname(os.path.realpath(__file__))
root = os.path.dirname(folder)
src = os.path.join(root, "src")

sys.path.insert(0, src)
