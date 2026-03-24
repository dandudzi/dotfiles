#!/bin/bash
# Reads jcodemunch token savings and outputs a status line fragment
SAVINGS_FILE="$HOME/.code-index/_genuine_savings.json"

if [ -f "$SAVINGS_FILE" ]; then
  node -e "
    const s = require('$SAVINGS_FILE');
    const tkns = s.total_genuine_tokens_saved || 0;
    const cost = (tkns / 1000000 * 25).toFixed(2);
    if (tkns >= 1000000) {
      console.log(((tkns/1000000).toFixed(1)) + 'M tkns saved · \$' + cost + ' saved');
    } else if (tkns >= 1000) {
      console.log(((tkns/1000).toFixed(1)) + 'K tkns saved · \$' + cost + ' saved');
    } else if (tkns > 0) {
      console.log(tkns + ' tkns saved · \$' + cost + ' saved');
    }
  " 2>/dev/null
fi
