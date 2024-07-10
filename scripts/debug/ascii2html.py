from guis.utils import ascii2html

str = \
"""
\u001b(CUnsupported ANSI code
\u001b(BUSASCII charset
\u001b[mNothing\u001b[m
\u001b[2mFaintEmptyReset\u001b[m
\u001b[1mBold\u001b[0m
\u001b[3mItalic\u001b[0m
\u001b[1;;3mBoldResetItalic\u001b[0m
\u001b[4mUnderline\u001b[0m
\u001b[21mDoubleUnderline\u001b[0m
\u001b[8mHidden\u001b[0m (Hidden)
\u001b[31m\u001b[42mRedOnGreen\u001b[0m
\u001b[32;41mGreenOnRed\u001b[0m
\u001b[92;101mBrightGreenOnBrightRed\u001b[0m
\u001b[38;2;255;0;0;48;2;0;0;255mTruecolorRedOnBlue\u001b[0m
\u001b[38;5;93;48;5;189m256Color\u001b[0m
\u001b[38;5;235;48;5;245m256ColorGraysacle\u001b[0m
"""

print(str)

print(ascii2html.translate(str).replace('<br/>', '\n').replace('\u001b', '○'))