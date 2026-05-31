---
tags:
    - Api
    - Code-generation
---

# Preprocessor

`jaff.codegen.preprocessor.Preprocessor`

The `Preprocessor` class fills marked sections of template source files with generated content before they are compiled or used. Placeholder blocks are defined in templates using pragma comments, and the preprocessor replaces them with the values provided. Any files not listed in `fnames` are passed through untouched.

**Pragma syntax** (configurable comment prefix):

```
!! PREPROCESS_RATES
!! PREPROCESS_END
```

Everything between `PREPROCESS_RATES` and `PREPROCESS_END` gets replaced with `dictionary["RATES"]`.

## Constructor

`#!python Preprocessor()`

No parameters. Initializes the internal logger.
