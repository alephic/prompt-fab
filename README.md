# PromptFab 🛠️

PromptFab is a toolkit that helps with creating reusable templates for prompting large language models.

PromptFab lets you write prompts that express the same underlying data schema in multiple formats without a bunch of boilerplate.

## Examples

```python
from prompt_fab import *

template = Prefix(
    'Please answer the following questions.\n\n',
    Repeat(
        Record(
            question=Affix(
                'Q: ', SENTENCE, EOL
            ),
            answer=Affix(
                'A: ', SENTENCE
            )
        ),
        delimiter='\n\n'
    )
)

data = [
    {
        'question': 'What year was Aubrey Plaza born?',
        'answer': '1984'
    },
    {
        'question': 'What should I have for breakfast?',
        'answer': 'You should have a banana.'
    }
]

print(template.fill(data))
```
Output:
```
Please answer the following questions.

Q: What year was Aubrey Plaza born?
A: 1984

Q: What should I have for breakfast?
A: You should have a banana.
```
PromptFab templates also allow parsing surface strings back into the data schema:
```python
assert data == template.match(template.fill(data))
```

An example of a prompt for a discriminative task:
```python
from prompt_fab import *

data = {
    'premise': "I'm the best magician in the world.",
    'hypothesis': "I can do magic.",
    'label': True
}

template = Record(
    premise=Suffix(SENTENCE, EOL),
    hypothesis=Affix('Hypothesis: ', SENTENCE, EOL),
    label=Prefix('Does this hypothesis follow? ',
        Option({True: 'Yes', False: 'No'})
    )
)

print(template.fill(data))
```
Output:
```
I'm the best magician in the world.
Hypothesis: I can do magic.
Does this hypothesis follow? Yes
```

## Computing scores

PromptFab also includes helper functions in the `prompt_fab.lm_openai` module that let you compute the model scores of particular prompt completions using OpenAI model API calls. Make sure to have the `OPENAI_API_KEY` environment variable set, set `openai.api_key_path` in your own code, or place your OpenAI API key in a file `openai_api_key.txt` in this module's root directory.

```python
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
```
Output:
```
[' Yes'] [-0.03768289]
```
This log-likelihood corresponds to a probability of 96%, so it looks like GPT-3 agrees that you can eat soup with a spoon.

For more details on the provided template building blocks,
refer to the docstrings in `prompt_fab.templates`.