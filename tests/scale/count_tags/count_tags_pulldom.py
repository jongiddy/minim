import sys

from xml.dom import pulldom


def run(doc):
    start_element = pulldom.START_ELEMENT
    count = 0
    for event, node in doc:
        if event == start_element:
            count += 1
    return count


def main():
    filename = sys.argv[1]
    if filename.endswith('.gz'):
        raise NotImplementedError('gzip not supported')
    else:
        doc = pulldom.parse(filename)
    count = run(doc)
    print(count)

if __name__ == '__main__':
    main()
