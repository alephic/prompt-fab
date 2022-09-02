from prompt_fab import *
from prompt_fab.lm_openai import get_template_completion_tokens_and_logprobs

template = Prefix(
    'Answer "Yes" or "No" to the following questions.\n\n',
    Repeat(
        Record(
            question=Affix('Q: ', SENTENCE, EOL),
            answer=Prefix('A: ', YES_NO)
        ),
        delimiter='\n\n'
    )
)

context_examples = [
    {'question': 'Is the sky blue?', 'answer': True},
    {'question': 'Can fish play basketball?', 'answer': False}
]

query = 'Can you eat soup with a spoon?'

# Pass in both partial data (just the context examples and query)
# as well as the full data including the target label that we want
# the likelihood of. Only one API call is made.
tokens, scores = get_template_completion_tokens_and_logprobs(
    template,
    context_examples+[{'question': query, 'answer': None}],
    context_examples+[{'question': query, 'answer': True}]
)
print(tokens, scores)