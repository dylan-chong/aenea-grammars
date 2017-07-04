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

# TODO remove this?
GRAMMAR_NAME = 'charwise_vim'
GRAMMAR_TAGS = [GRAMMAR_NAME + '.all']

CHAR_KEY_MAPPINGS = {  # TODO move this into an aenea file?
    # In each sub-key: What to say (key): Dragon key code (value)
    'all': {},  # Updated below
    'uppercase_letters': None,  # Updated below
    # TODO control/alt
    'lowercase_letters': {
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
        'poppa': 'p',
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
        # Brackets and stuff
        'left (paren|parenthesis)': 'lparen',
        'right (paren|parenthesis)': 'rparen',
        'left bracket': 'lbracket',
        'right bracket': 'rbracket',
        'left brace': 'lbrace',
        'right brace': 'rbrace',
        '(less than|left angle)': 'leftangle',
        '(greater than|right angle)': 'rightangle',
        # Quotes
        '[single] quote': 'squote',
        'double quote': 'dquote',
        'backtick': 'backtick',
        # Slashes
        'backslash': 'backslash',
        'forward slash': 'slash',
        # Shift + Keys 1-8
        'exclamation [mark]': 'exclamation',
        'at [sign]': 'at',
        # TODO LATER finish keys 3-8
        # Spaces
        'space [bar]': 'space',
        'tab': 'tab',
        # Other
        '(full stop|dot)': 'dot',
        'comma': 'comma',
        'question [mark]': 'question',
        '(dash|hyphen|minus)': 'minus',
        '(underscore|score)': 'minus',
        'equals': 'equals',
        'plus': 'plus',
        'colon': 'colon',
        'semicolon': 'semicolon',
        '[vertical] bar': 'bar',
        },
    'digits': {
        ('dig ' + word): num for word, num in {
        'zero': '0',
        'one': '1',
        'two': '2',
        'three': '3',
        'four': '4',
        'five': '5',
        'six': '6',
        'seven': '7',
        'eight': '8',
        'niner': '9'
            }.iteritems()
        }
    }
UPPERCASE_KEY_PREFIX = 'big '

charwise_grammar = None


# Setup


def load():
    print 'Loading _charwise_vim.py'

    global charwise_grammar
    charwise_grammar = setup_grammar()


def unload():
    aenea.vocabulary.inhibit_global_dynamic_vocabulary(GRAMMAR_NAME, GRAMMAR_TAGS)

    global charwise_grammar
    if charwise_grammar:
        charwise_grammar.unload()
    charwise_grammar = None


def setup_key_mappings():
    # See the Dragonfly documentation to see what the values should be:
    # http://dragonfly.readthedocs.io/en/latest/_modules/dragonfly/actions/action_key.html?highlight=lparen
    # Not all symbols are here. Feel free to add the ones you need
    CHAR_KEY_MAPPINGS['uppercase_letters'] = {
        UPPERCASE_KEY_PREFIX + speech: 's-' + letter
        for speech, letter in CHAR_KEY_MAPPINGS['lowercase_letters'].iteritems()
        }

    for sub_mappings in {s for s in CHAR_KEY_MAPPINGS.keys() if s != 'all'}:
        CHAR_KEY_MAPPINGS['all'].update(CHAR_KEY_MAPPINGS[sub_mappings])


def setup_grammar():
    vim_context = create_app_context()
    new_grammar = Grammar(GRAMMAR_NAME, context=vim_context)
    aenea.vocabulary.uninhibit_global_dynamic_vocabulary(GRAMMAR_NAME, GRAMMAR_TAGS)

    new_grammar.add_rule(CharwiseVimRule())
    new_grammar.load()

    return new_grammar


def create_app_context():
    # Allow use with IntelliJ's IDEA-Vim plugin (this is quite general so it
    # may match other apps accidentally)
    intellij_window_title = '[^\s]+ - [^\s]+ - \[[^\s]+\]'
    # iTerm 2 sets the window title to these
    terminal_window_names = 'BASH|RUBY|PYTHON'

    return aenea.wrappers.AeneaContext(
        ProxyAppContext(
            match='regex',
            title='(?i).*(?:VIM|' + terminal_window_names + ').*' +
                  '|(?:' + intellij_window_title + ')'
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
    mapping['down'] = 'j'

    def value(self, node):
        return Key(MappingRule.value(self, node))


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
    }


class CharwiseVimRule(CompoundRule):
    """
    The top level rule.

    Allows for saying multiple commands at once, but will end
    after dictating words (see :class:`~TextEntryRule`)
    """
    repeated_rules_key = 'repeated_rules'
    spec = '<{}>'.format(repeated_rules_key)  # TODO End with TextEntryRule
    _repeatable_rules = [
        RuleRef(SingleCharRule()),
        RuleRef(SimpleCommandRule()),
        ]
    extras = [
        # TODO put with count
        Repetition(
            Alternative(_repeatable_rules),
            max=20,
            name=repeated_rules_key
            )
        ]

    def _process_recognition(self, node, extras):
        print 'CharwiseVimRule._process_recognition(\n  {}, \n  {}, \n  {})'\
            .format(self, node, extras)

        for key in extras[self.repeated_rules_key]:
            print 'Executing {}'.format(key)
            key.execute()

load()

