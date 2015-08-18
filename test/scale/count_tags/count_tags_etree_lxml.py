import sys

from lxml import etree as ElementTree


def run(doc):
    count = 0
    for element in doc.iter():
        count += 1
    return count


def main():
    filename = sys.argv[1]
    if filename.endswith('.gz'):
        raise NotImplementedError('gzip not supported')
    else:
        tree = ElementTree.parse(filename)
        root = tree.getroot()
    count = run(root)
    print(count)

if __name__ == '__main__':
    main()
