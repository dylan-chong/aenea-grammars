import aenea.config
import aenea.misc
import aenea.vocabulary

from aenea import (
    Key,
    NoAction,
    Text
)

from aenea.proxy_contexts import ProxyAppContext

from dragonfly import (
    Alternative,
    AppContext,
    CompoundRule,
    Dictation,
    Grammar,
    MappingRule,
    Repetition,
    RuleRef
)

GRAMMAR_NAME = 'charwise_vim'
INHIBITED_GRAMMAR_TAGS = ["vim.insertions", "multiedit.count", "global"]

CHAR_KEY_MAPPINGS = {  # TODO move this into a separate importable grammar file?
    # See the Dragonfly documentation to see what the values should be:
    # http://dragonfly.readthedocs.io/en/latest/_modules/dragonfly/actions/action_key.html?highlight=lparen
    # Not all symbols are here. Feel free to add the ones you need

    # In each sub-key: What to say (key): Dragon key code (value)
    'all': {},  # All mappings excluding modifier keys. Updated below
    'letters': {
        # Copied from aenea/client/misc.py
        'alpha': 'a',
        'bravo': 'b',
        'charlie': 'c',
        'delta': 'd',
        'echo': 'e',
        'foxtrot': 'f',
        'golf': 'g',
        'hotel': 'h',
        'indigo': 'i',
        'juliet': 'j',
        'kilo': 'k',
        'lima': 'l',
        'mike': 'm',
        'november': 'n',
        'oscar': 'o',
        'poppy': 'p',  # Different from 'poppa' (avoids conflict with 'proper')
        'quiche': 'q',
        'romeo': 'r',
        'sierra': 's',
        'tango': 't',
        'uniform': 'u',
        'victor': 'v',
        'whiskey': 'w',
        'x-ray': 'x',
        'yankee': 'y',
        'zulu': 'z'
    },
    'symbols': {
        # NOTES:
        # vocabulary_config/symbols.json has many symbols, but they
        # don't get 'mixed in' with this grammar, so you have to wait if you
        # do something like 'foxtrot ash' ('f/') - you have to wait for the
        # 'foxtrot' to be recognised before saying 'ash'.
        # TODO there has got to be a better way than duplicating everything

        # Brackets and stuff
        'left (paren|parenthesis)': 'lparen',
        'right (paren|parenthesis)': 'rparen',
        'left bracket': 'lbracket',
        'right bracket': 'rbracket',
        'left brace': 'lbrace',
        'right brace': 'rbrace',
        '(less than|left angle)': 'langle',
        '(greater than|right angle)': 'rangle',
        # Quotes
        '[single] quote': 'squote',
        '(double|dub) quote': 'dquote',
        'backtick': 'backtick',
        # Slashes
        'backslash': 'backslash',
        '[forward] slash': 'slash',
        # Shift + Keys 1-8
        '(exclamation [mark]|bang)': 'exclamation',
        'at sign': 'at',
        '(hash|pound)': 'hash',
        'dollar': 'dollar',
        'percent': 'percent',
        'caret': 'caret',
        '(ampersand|amp)': 'ampersand',
        '(asterisk|star)': 'asterisk',
        # Spaces
        'space [bar]': 'space',
        'tab': 'tab',
        '(enter|new line)': 'enter',
        # Other
        '(full stop|dot)': 'dot',
        'comma': 'comma',
        'question [mark]': 'question',
        'underscore': 'underscore',
        '(dash|hyphen|minus)': 'minus',
        'colon': 'colon',
        '(pipe|vertical bar)': 'bar',
        '(equals|equal)': 'equal',
        'plus': 'plus',
        # Semicolon does not exist in dragonfly 0.6.5.
        # There is a SimpleCommandRule to get around this
    },
    'digits': {
        'zero': '0',
        'one': '1',
        'two': '2',
        'three': '3',
        'four': '4',
        'five': '5',
        'six': '6',
        'seven': '7',
        'eight': '8',
        '(niner|nine)': '9'
        }
    }


charwise_grammar = None


# Setup


def load():
    print 'Loading _charwise_vim.py'

    global charwise_grammar
    charwise_grammar = setup_grammar()


def unload():
    global charwise_grammar
    if charwise_grammar:
        charwise_grammar.unload()
        aenea.vocabulary.uninhibit_global_dynamic_vocabulary(
            GRAMMAR_NAME, INHIBITED_GRAMMAR_TAGS
            )
    charwise_grammar = None


def setup_key_mappings():
    # Copy into CHAR_KEY_MAPPINGS['all']
    for sub_mappings in {s for s in CHAR_KEY_MAPPINGS.keys() if s != 'all'}:
        CHAR_KEY_MAPPINGS['all'].update(CHAR_KEY_MAPPINGS[sub_mappings])


def setup_grammar():
    vim_context = create_app_context()
    new_grammar = Grammar(GRAMMAR_NAME, context=vim_context)

    # TODO does this prevent other vocabs from using the global grammars
    aenea.vocabulary.inhibit_global_dynamic_vocabulary(
        GRAMMAR_NAME, INHIBITED_GRAMMAR_TAGS
        )

    new_grammar.add_rule(CharwiseVimRule())
    new_grammar.load()

    return new_grammar


def create_app_context():
    # Allow use with IntelliJ's IDEA-Vim plugin (this is quite general so it
    # may match other apps accidentally)
    intellij_window_title = '[\S]+ - [\S]+ - \[\S+\]'
    # iTerm 2 sets the window title to these when using Vim/Neovim.
    # We might want to `set editing-mode vi` in the terminal, so we need to
    # match Bash.
    terminal_window_names = 'BASH|ZSH|RUBY|PYTHON\d?'
    # IntelliJ (Mac) has no window title when there's any sort of popup
    # window (e.g. autocomplete, find in files, etc), so we need to match an
    blank_window_title = '\s*'
    intellij_app_name = 'idea|intellij.*'  # TODO appcode, rubymine, pycharm ?

    return aenea.wrappers.AeneaContext(
        ProxyAppContext(
            match='regex',
            title='(?i).*(?:VIM|' + terminal_window_names + ').*' +
                  '|(?:' + intellij_window_title +
                  '|' + blank_window_title + ')',
            app_id='(?i).*VIM.*|.*TERM.*|' + intellij_app_name,
            ),
        AppContext(title='VIM')
        )


# Rules


class SingleCharRule(MappingRule):
    """
    Allows the entry of a single character. See aenea/client/aenea/misc.py for
    what word(s) you have to say for each character.
    """
    setup_key_mappings()
    mapping = CHAR_KEY_MAPPINGS['all']


class ModifierKeyRule(MappingRule):
    mapping = {
        # grammar to modifier for use in Key, e.g. Key('s-a')
        '(shift|big)': 's',
        '(control|con)': 'c',
        '(alt|olt)': 'a',  # use 'olt` as hack for proper pronunciation of 'alt'
        '(windows|command)': 'w',  # Command key on Mac
    }


class ModifiableSingleCharRule(CompoundRule):
    """
    A SingleCharRule with optional modifier keys
    """
    spec = '[<ModifierKeyRule>] <SingleCharRule>'
    extras = [
        RuleRef(ModifierKeyRule(), name='ModifierKeyRule'),
        RuleRef(SingleCharRule(), name='SingleCharRule'),
    ]

    def value(self, node):
        # Seriously, what kind of api makes you write this sort of shit?
        children = node.children[0].children[0].children
        optional_modifier = children[0].value()
        char = children[1].value()

        if optional_modifier:
            key_str = '{}-{}'.format(optional_modifier, char)
        else:
            key_str = char

        return Key(key_str)


class SimpleCommandRule(MappingRule):
    """
    Similar to SingleCharRule, but you can include non-symbol things like
    pressing 'Escape', or 'Control-D'.
    """
    setup_key_mappings()
    mapping = {
        '(escape|quit)': Key('escape'),
        'backspace': Key('backspace'),
        'up': Key('up'),
        'down': Key('down'),
        'left': Key('left'),
        'right': Key('right'),
        '(page up|gup)': Key('c-u'),
        '(page down|gone)': Key('c-d'),
        'semicolon': Text(';'),  # Gets around the invalid Key('semicolon')
    }


# TODO include programming.json somewhere??


def format_snakeword(text):
    formatted = text[0][0].upper()
    formatted += text[0][1:]
    formatted += ('_' if len(text) > 1 else '')
    formatted += format_score(text[1:])
    return formatted


def format_score(text):
    return '_'.join(text)


def format_camel(text):
    return text[0] + ''.join([word[0].upper() + word[1:] for word in text[1:]])


def format_proper(text):
    return ''.join(word.capitalize() for word in text)


def format_relpath(text):
    return '/'.join(text)


def format_abspath(text):
    return '/' + format_relpath(text)


def format_scoperesolve(text):
    return '::'.join(text)


def format_jumble(text):
    return ''.join(text)


def format_dotword(text):
    return '.'.join(text)


def format_dashword(text):
    return '-'.join(text)


def format_natword(text):
    return ' '.join(text)


def format_broodingnarrative(text):
    return ''


def format_sentence(text):
    return ' '.join([text[0].capitalize()] + text[1:])


class IdentifierInsertion(CompoundRule):
    """
    Text insertion. E.g. saying 'camel my variable name' => types
    'myVariableName'.
    """
    spec = ('[upper | natural] ( proper | camel | rel-path | abs-path | score '
            '| sentence | scope-resolve | jumble | dotword | dashword | '
            'natword | snakeword | brooding-narrative) [<dictation>]')
    extras = [Dictation(name='dictation')]

    def value(self, node):
        words = node.words()

        uppercase = words[0] == 'upper'
        lowercase = words[0] != 'natural'

        if lowercase:
            words = [word.lower() for word in words]
        if uppercase:
            words = [word.upper() for word in words]

        words = [word.split('\\', 1)[0].replace('-', '') for word in words]
        if words[0].lower() in ('upper', 'natural'):
            del words[0]

        func = globals()['format_%s' % words[0].lower()]
        formatted = func(words[1:])

        return Text(formatted)


class CharwiseVimRule(CompoundRule):
    """
    The top level rule.

    Allows for saying multiple commands at once, but will end
    after dictating words (see :class:`~TextEntryRule`)
    """
    _repeated_rules_key = 'repeated_rules'
    _identifier_insertion_key = 'identifier_insertion'

    _repeatable_rules = [
        RuleRef(ModifiableSingleCharRule()),
        RuleRef(SimpleCommandRule()),
        ]

    spec = '[<{}>] [<{}>]'.format(_repeated_rules_key, _identifier_insertion_key)
    extras = [
        Repetition(
            Alternative(_repeatable_rules),
            max=20,
            name=_repeated_rules_key
            ),
        RuleRef(IdentifierInsertion(), name=_identifier_insertion_key)
        ]

    def _process_recognition(self, node, extras):
        # If node contains a string, but extras contains 'None', then perhaps
        # you have tried to call Key(str) where 'str' is some invalid key name.
        print '_process_recognition(\n  node={},\n  extras={}\n)'\
            .format(node, extras)

        # Press keys for what user just said
        if self._repeated_rules_key in extras:
            for key_or_text in extras[self._repeated_rules_key]:
                if key_or_text:
                    print 'Executing Repeatable {}'.format(key_or_text)
                    key_or_text.execute()

        if self._identifier_insertion_key in extras:
            identifier = extras[self._identifier_insertion_key]
            print 'Executing Identifier {}'.format(identifier)
            identifier.execute()

load()

