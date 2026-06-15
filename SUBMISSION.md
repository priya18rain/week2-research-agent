


Design Decisions:
1.set max characters as 3000 instead of say 8000, to prevent token loss.
2.added promps like
    - Base answers only on tool results.
    - Do not add facts that are not present in tool outputs.
    - If information is missing, say it is missing.
cause the output seemed to be "hallucinating based on previous answers"

I was not able to attempt implementing Alpha Xiv MCP Server properly, so if given more time, I would definetely try to complete that