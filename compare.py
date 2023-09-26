import argparse
import sys
import os
from three_scan import three_scan


def main():
    parser = argparse.ArgumentParser(prog="3DScan",
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument("-i", "--input", dest="input", metavar="path", action='append', required=True,
                        help="path of input models."
                        "Example usage: --input game_a --input game_b")
    parser.add_argument("-a", "--animation", dest="animation", metavar="bool", type=bool, required=False, default=False,
                        help="compare Animation or not."
                        " The default value is False")
    parser.add_argument("-o", "--output", dest="output", metavar="path", type=str, default="result.json",
                        help="path of output result JSON file."
                        "If --animation flag is present, an additional animation comparision result will be produced.")

    args = parser.parse_args()
    input_path = args.input
    animation_flag = args.animation
    output_path = args.output

    # test input
    if not (len(input_path) == 1 or len(input_path) == 2):
        print("[main] error: invalid input path", file=sys.stderr)
        os._exit(-1)
    else:
        for i in input_path:
            if not os.path.exists(i):
                print("[main] error: invalid input path", file=sys.stderr)
                os._exit(-1)
            if not os.path.isdir(i):
                print(f"[main] error: input {i} should be a directory", file=sys.stderr)

    if animation_flag == True:
        if len(input_path) != 2:
            print("[main] error: --input should be used twice", file=sys.stderr)
            os._exit(-1)
        three_scan.scan_and_compare(input_path, output_path)
    else:
        if len(input_path) != 1:
            print("[main] warning: --input shall be used only once, addition flag is ignored", file=sys.stderr)
        three_scan.scan(input_path[0], output_path)


if __name__ == "__main__":
    main()

