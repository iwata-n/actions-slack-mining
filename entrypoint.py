#!/bin/python
import os

print('Hello World')
for e in os.environ:
  print(e)
print('---')

with open(os.environ['GITHUB_EVENT_PATH']) as f:
  s = f.read()
  print(s)
