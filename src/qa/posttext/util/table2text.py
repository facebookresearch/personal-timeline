import os
import sys
import pandas as pd


def verbalize(episodes, template):
    all_text = []
    numcols = len(episodes.columns)
    for idx, row in episodes.iterrows():
        s = template.format(**row)
        all_text.append(s)

    return all_text

def main(argv):

    episodes = pd.read_csv(argv[0])
    template = argv[1]

    textdata = verbalize(episodes, template)

    text_file = open(argv[0]+".txt", "w")
    for s in textdata:
        text_file.write(s)
        text_file.write("\n")
    text_file.close()


if __name__ == "__main__":
    main(sys.argv[1:])
