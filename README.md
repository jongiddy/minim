# minim
Tokenizer for XML-like files

The minim package reads a file and emits tokens that are based on the XML
standard.  The tokenizer is structured to minimise the amount of memory
allocation.

The tokens are read through a generator.  Each call to the generator's `next()`
method yields a token_type indicating the type of token read.  To obtain the
actual token, the caller must use the `get_token()` method of the generator.

To print the non-markup content of an XML file, we could use:

```python

for token in minim.lex.tokens(string_iter):
	if token.is_content:
		sys.stdout.write(token.content)
```

However, this will allocate memory for each token in the file.

A more efficient way to do this is to use:

```python

token_types = minim.lex.token_types(string_iter)
for token_type in token_types:
	if token_type.is_content:
		token = token_types.get_token(token_type)
		sys.stdout.write(token.content)
```

This will allocate memory only for the content tokens to be displayed.

For the ultimate in memory allocation reduction, add a ``token`` parameter to
the ``get_token`` call:

```python

content_token = minim.tokens.Content()
token_types = minim.lex.token_types(string_iter)
for token_type in token_types:
	if token_type.is_content:
		token = token_types.get_token(token_type, content_token)
		sys.stdout.write(token.content)
```

This allocates a single token class, which is re-used for each content token.

As you can see, memory efficiency comes at the price of added complexity.
Choose wisely.
