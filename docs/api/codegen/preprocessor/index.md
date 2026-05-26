---
tags:
    - Api
    - Code-generation
---

# Preprocessor

`jaff.codegen.preprocessor.Preprocessor`

Pragma-based template preprocessor. Replaces `PREPROCESS_KEY` pragma blocks in template files with values from a dictionary, then writes the result to a build directory. Files not in `fnames` are copied unchanged.

**Pragma syntax** (configurable comment prefix):

```
!! PREPROCESS_RATES
!! PREPROCESS_END
```

Content between `PREPROCESS_RATES` and `PREPROCESS_END` is replaced with `dictionary["RATES"]`.

## Constructor

`#!python Preprocessor()`

No parameters. Initializes the internal logger.
