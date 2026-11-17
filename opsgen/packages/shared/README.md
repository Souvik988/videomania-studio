# @opsgen/shared

What OpsGen's clients share: a chat turn and the events a client sees, how an agent's activity reads, prompt
references, title limits and Markdown parsing.

```ts
import { buildPromptDisplay, type Turn } from '@opsgen/shared';
import { scanMarkdownBlocks } from '@opsgen/shared/markdown';
```

Part of [OpsGen](https://github.com/openfilm/openfilm). MIT licensed.
