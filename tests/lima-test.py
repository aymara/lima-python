#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2022 CEA LIST <gael.de-chalendar@cea.fr>
#
# SPDX-License-Identifier: MIT

# -*- coding: utf-8 -*-

import aymara.lima

lima = aymara.lima.Lima()
result = lima.analyzeText("This is a text on 02/05/2022.", lang="eng", pipeline="main")
print(result.conll())

