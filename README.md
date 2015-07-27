# minim
Tokenizer for XML-like files

The minim package reads a file and emits tokens that are based on the XML
standard.  The tokenizer is structured to minimise the amount of memory
allocation.

The tokens are read through a generator.  Each call to the generator's `next()`
method yields a token indicating the type of text read.  To obtain the
actual text, the caller must use the `get_text()` method of the generator.

To print the non-markup content of an XML file, we can use:

```python

token_stream = minim.lex.TokenScanner.from_strings(string_iter)
for token in token_stream:
    text = token_stream.get_text(token)
    if token.is_content:
        sys.stdout.write(text.content())
```

Since the text is only used if the token is content,
we can avoid wasteful allocations of the text object by moving it inside the `if` statement.
This avoids a couple of memory allocations
(creating the TextHolder object and slicing the string out of the buffer):

```python

token_stream = minim.lex.TokenScanner.from_strings(string_iter)
for token in token_stream:
    if token.is_content:
        text = token_stream.get_text(token)
        sys.stdout.write(text.content())
```

To reduce memory allocation further,
add a ``holder`` parameter to the ``get_text`` call:

```python

holder = minim.tokens.TextHolder()
token_stream = minim.lex.TokenScanner.from_strings(string_iter)
for token in token_stream:
    if token.is_content:
        text = token_stream.get_text(token, holder)
        sys.stdout.write(text.content())
```

This allocates a single TextHolder class,
which is re-used for each content token.
The returned `text` object is (usually) the same as the `holder` object,
but with the text value for the current token.

Note that the string slicing is still performed for all content text objects.
Removing that is future work,
which may be avoided by converting this library to a compiled module
(written in C, D, or Rust).
