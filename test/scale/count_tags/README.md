Count the number of tags in a file. This includes all start and empty tags, but
not the end tags.

Note, on Ubuntu 14.04 with Python 3.4.0, the `-O` flag made the first 3 tests, using existing libraries, slightly slower than without the flag.
Hence, they have been done without the `-O` flag.

Timings as of 2015-07-19:

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

$ time PYTHONPATH=${MINIM_HOME}/python3 python3 -O count_tags_minim.py ../xml/gb_20140923.xml
222392

real    0m14.397s
user    0m14.363s
sys     0m0.029s


$ time PYTHONPATH=${MINIM_HOME}/python3 python3 -O count_tags_minim_simple.py ../xml/gb_20140923.xml
222392

real    0m20.899s
user    0m20.863s
sys     0m0.013s


$ time PYTHONPATH=${MINIM_HOME}/python3 python3 -O count_tags_minim_ns.py ../xml/gb_20140923.xml
222392

real    0m21.564s
user    0m21.570s
sys     0m0.004s

```


There's a long way to go, speed-wise!  But at least the answers match...
