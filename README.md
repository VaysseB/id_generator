# Identifier generator
Identifier generator based on expression, inspired by regular expression but for text generation.

## Requirement

It runs with Python 3.

It was made with Python 3.6, but I didn't check for older version.

## Usage

The generator requires an expression to create random identifier.

Right now, it support fixed text sequences and number generation. It is inpired by regular expression syntax.

By default, it will try to produce 20 unique identifiers but this can be changed with `-c` or `--count` option. It is possible that the generator will produce less than asked, in case that the expression cannot produce such amount. Example: "[1-5]" can only produce 5 different outputs.


## Examples

```bash

    $ python idgen.py "MPL-[1-999|z]-IDR-[1-4]" --count 5
    MPL-665-IDR-3
    MPL-563-IDR-1
    MPL-090-IDR-3
    MPL-181-IDR-4
    MPL-272-IDR-4
    
    $ python idgen.py "DOC-[1-5|3z]" -c 5
    DOC-002
    DOC-001
    DOC-005
    DOC-003
    DOC-004
    
```