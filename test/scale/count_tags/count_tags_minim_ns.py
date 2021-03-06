import sys

from minim import nslex, tokens


def run(doc):
    start_element = tokens.StartOrEmptyTagOpen
    count = 0
    scanner = nslex.NamespaceTokenScanner.from_strings(doc)
    for token in scanner:
        if isinstance(token, start_element):
            count += 1
    return count


def main():
    filename = sys.argv[1]
    if filename.endswith('.gz'):
        import gzip
        f = gzip.open(filename, 'rt', encoding='utf-8')
    else:
        f = open(filename, 'rt', encoding='utf-8')
    try:
        count = run(f)
    finally:
        f.close()
    print(count)

if __name__ == '__main__':
    main()
