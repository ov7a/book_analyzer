# coding: utf-8

import nltk

nltk.data.path.append(".")
from nltk.corpus import wordnet
from nltk.corpus import stopwords
from collections import defaultdict
import re
import itertools
import epub
import sys
from html.parser import HTMLParser

regex = re.compile(r"[^\w]+")
english_stopwords = set(stopwords.words('english'))


def lemmatize(word):
    lemmed = wordnet.morphy(word.lower())
    if lemmed is None:
        return word
    return lemmed


def get_frequencies(text):
    words = sorted(map(lemmatize, filter(lambda x: len(x) and x.lower() not in english_stopwords, regex.split(text))))
    frequencies = map(lambda x: (x[0], len(list(x[1]))), itertools.groupby(words))
    return list(frequencies)


def merge_frequencies(*args):
    all = defaultdict(int)
    for word, freq in itertools.chain(*args):
        all[word] += freq
    return list(all.items())


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = ""

    def handle_data(self, data):
        self.data += data


def extract_text(html):
    parser = TextExtractor()
    parser.feed(html)
    return parser.data


def load_file(fname):
    book = epub.Book(epub.open_epub(fname))
    return book


def get_list_of_refs(book):
    guide = book.epub_file.opf.guide
    return guide.references


def get_book_frequencies(book, goodrefs):
    all_freqs = list()
    for chapter in book.chapters:
        href = chapter._manifest_item.href
        # FIXME
        # if href not in goodrefs:
        #    continue
        html = chapter.read().decode("utf-8")
        text = extract_text(html)
        all_freqs.append(get_frequencies(text))
    aggregated = merge_frequencies(*all_freqs)
    aggregated.sort(key=lambda x: -x[1])
    return aggregated

def write_frequencies(aggregated, fname):
    total = sum(map(lambda x: x[1], aggregated))
    with open(fname + ".frequencies.txt", "w") as f:
        f.write("TOTAL - %d\n" % total)
        for word, freq in aggregated:
            f.write("%s - %d\n" % (word, freq))

    aggregated.sort(key=lambda x: x[0].lower())
    with open(fname + ".frequencies_ab.txt", "w") as f:
        f.write("TOTAL - %d\n" % total)
        for word, freq in aggregated:
            f.write("%s - %d\n" % (word, freq))


if __name__ == "__main__":
    command = sys.argv[1]
    fnames = sys.argv[2:]
    all = list()

    for fname in fnames:
        print("\nProcessing", fname)
        book = load_file(fname)
        refs = get_list_of_refs(book)
        if command == "list":
            for ref in refs:
                print(ref)
        else:
            # prefix=sys.argv[2]

            #FIXME: does not work
            goodrefs = refs  # set(filter(lambda href: href.startswith(prefix), map(lambda x: x[0], refs)))

            aggregated = get_book_frequencies(book, goodrefs)
            all.append(aggregated)
            write_frequencies(aggregated, fname)

    if command != "list":
        all_freq = merge_frequencies(*all)
        all_freq.sort(key=lambda x: -x[1])
        write_frequencies(all_freq, "total")