# NOTE: Merged with [aioreq](https://github.com/karosis88/aioreq)

# Rfcparser
Rfcparser is a Python tool that makes it easy to parse common RFC syntaxes. Rfcparser takes a raw string as input, parses, validates, and returns Python objects to simplify the processing of RFC syntaxes.

## Overview
This library uses grammar parsing mechanism to effectively parse various RFC syntaxes and make the information accessible in a usable format. 

### Examples

This is how **RFC 3986** defines URI syntax
```
URI           = scheme ":" hier-part [ "?" query ] [ "#" fragment ]

hier-part     = "//" authority path-abempty
                 / path-absolute
                 / path-rootless
                 / path-empty

URI-reference = URI / relative-ref

absolute-URI  = scheme ":" hier-part [ "?" query ]
...
```
This is how **rfcparser** does
```
uri           : scheme ":" hier_part [ "?" query ] [ "#" fragment ]
hier_part     : "//" authority path_abempty
                | path_absolute
                | path_rootless
                | path_empty
uri_reference : uri | relative_ref

absolute_uri  : scheme ":" hier_part [ "?" query ]
...
```

---

This is how **RFC 1034** defines domain syntax
```
<domain> ::= <subdomain> | " "
<subdomain> ::= <label> | <subdomain> "." <label>
<label> ::= <letter> [ [ <ldh-str> ] <let-dig> ]
<ldh-str> ::= <let-dig-hyp> | <let-dig-hyp> <ldh-str>
<let-dig-hyp> ::= <let-dig> | "-"
<let-dig> ::= <letter> | <digit>
<letter> ::= any one of the 52 alphabetic characters A through Z in
upper case and a through z in lower case
```

This is how **rfcparser** does

```
domain      : subdomain | " "
subdomain   : _label | subdomain "."  _label
_label       : _letter [ [ _ldh_str ] _let_dig ]
_ldh_str     : _let_dig_hyp | _let_dig_hyp _ldh_str
_let_dig_hyp : _let_dig | "-"
_let_dig     : _letter | DIGIT
_letter      : /[a-zA-Z]/

%import .rfc5234_core.DIGIT
```

## Installing

```
$ pip install rfcparser
```
or 

```
$ git clone https://github.com/karosis88/rfcparser.git
$ pip install ./rfcparser
```

## Usage
Examples and detailed instructions on how to use the Rfcparser library to parse RFC syntaxes.

In most cases, you will primarily use the 'core' module, which offers a convenient interface for parsing your raw input string
``` python
>>> from rfcparser import core

```

Rfcparser offers a specific class for each grammar, with a class name following the pattern of "`PREFIX PARSER RFC-NUMBER`"

Fortunately, most modern IDEs now offer autocompletion, which will assist you in locating the parser classes you need to use.

### URI parsing


``` python
>>> uri = "https://login:password@127.0.0.1:1010/path?name=test#fr"
>>> parsed_uri = core.UriParser3986().parse(uri)

```

With Rfcparser, you now have access to a 'parsed_uri' that is not just a plain string, but rather a Python object. This makes it easier to work with the URI, and you don't need to worry about compatibility issues with other applications as the library parses syntaxes according to the latest RFC standards.

``` python
>>> parsed_uri.scheme
'https'
>>> parsed_uri.userinfo
'login:password'
>>> parsed_uri.ip
'127.0.0.1'
>>> parsed_uri.port
1010
>>> parsed_uri.path
'/path'
>>> parsed_uri.query
{'name': 'test'}
>>> parsed_uri.fragment
'fr'

```

### Date-Time parser

``` python
>>> date_str = "Tue, 07-Feb-2023 13:20:04 GMT"
>>> parsed_date = core.DateParser6265().parse(date_str)
>>> type(parsed_date)
<class 'datetime.datetime'>
>>> parsed_date.day
7

```


