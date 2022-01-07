#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aymara.lima

lima = aymara.lima.Lima()
result = lima.analyzeText("This is a text.", lang="eng", pipeline="main")
print(result)

