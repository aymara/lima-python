#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

# Let's suppose you have installed lima-python in a virtualenvwrapper
# environment named aymara
workon aymara

# Let's install the Wolof models
lima_models -i wol

# Check what models are available
lima_models -l

# Language (id )   Tokenizer Lemmatizer Morphosyntax
# ---
# english  (eng)   installed installed  installed
# wolof    (wol)   installed   empty    installed

# Test the newly installed language
lima -l ud-wol -p deepud examples/test-wol.txt
