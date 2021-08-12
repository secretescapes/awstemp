# awstemp

Command line interface for assuming AWS IAM roles and rewriting AWS Credentials and Config files.

## Installation

```
pipx install git+https://github.com/secretescapes/awstemp
```

## Autocomplete

`awstemp` comes with autocomplete! It can suggest profiles direct from your `~/.aws/credentials` file, and works with most commonly used shells.

You will need to install `argcomplete` in order to make use of this functionality. Installation instructions are available here: https://pypi.org/project/argcomplete/


Most common setups:


### `Bash`

```
register-python-argcomplete awstemp > /etc/bash_completion.d/awstemp
```

### `Zsh`

Add the following to your `~/.zshrc`

```
autoload -U bashcompinit
bashcompinit
eval "$(register-python-argcomplete awstemp)"
```


### `Fish`

```
register-python-argcomplete --shell fish awstemp > ~/.config/fish/completions/awstemp.fish
```
