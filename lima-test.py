#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import aymara.lima

lima = aymara.lima.Client(host="localhost", port="8080", container=False)
lima.list_models()
lima.list_installed_models()
# lima.install_model("mar")
print(aymara.lima.ps())
result = lima.analyzeText("hello", lang="ud-mar", pipeline="deepud")
