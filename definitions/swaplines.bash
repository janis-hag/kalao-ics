#!/bin/sed -f
/^keygroup/ {
:notdone
  N
  s/^\(keygroup[^\n]*\)\(\n\([^\n]*\n\)*\)\(keyword[^\n]*\)$/\4\2\1/
  t
  bnotdone
}
