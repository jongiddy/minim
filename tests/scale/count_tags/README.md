Count the number of tags in a file. This includes all start and empty tags, but
not the end tags.

Timings as of 2015-05-25:

```
$ time PYTHONPATH=${MINIM_HOME}/python3 python3 count_tags_etree_lxml.py ../xml/gb_20140923.xml
222392

real    0m0.391s
user    0m0.327s
sys     0m0.064s

$ time PYTHONPATH=${MINIM_HOME}/python3 python3 count_tags_etree.py ../xml/gb_20140923.xml
222392

real    0m0.721s
user    0m0.682s
sys     0m0.040s

$ time PYTHONPATH=${MINIM_HOME}/python3 python3 count_tags_pulldom.py ../xml/gb_20140923.xml
222392

real    0m7.941s
user    0m7.930s
sys     0m0.012s

$ time PYTHONPATH=${MINIM_HOME}/python3 python3 count_tags_minim.py ../xml/gb_20140923.xml
222392

real    0m17.765s
user    0m17.765s
sys     0m0.008s

$ time PYTHONPATH=${MINIM_HOME}/python3 python3 count_tags_minim_simple.py ../xml/gb_20140923.xml
222392

real	0m26.773s
user	0m26.777s
sys		0m0.008s

```

There's a long way to go, speed-wise!  But at least the answers match...
