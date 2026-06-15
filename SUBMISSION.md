I tried building a research tool that worked on the basic loop that was described-
user input, model calls web_search or web_fetch, result gets added back to conversation, model calls more tools or gives final answer.

Design Decisions:
1.set max characters as 3000 instead of say 8000, to prevent token loss. Also due to VS Code's own keybindings, Ctrl+K and Ctrl+Q were not working properly.
2.added promps like
    - Base answers only on tool results.
    - Do not add facts that are not present in tool outputs.
    - If information is missing, say it is missing.
cause the output seemed to be "hallucinating based on previous answers"

I was not able to attempt implementing Alpha Xiv MCP Server properly(OAuth issue), so if given more time, I would definetely try to complete that