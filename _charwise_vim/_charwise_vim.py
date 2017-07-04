import aenea.config
import aenea.misc
import aenea.vocabulary

from aenea import (
    Key
)

from aenea.proxy_contexts import ProxyAppContext

from dragonfly import (
    Alternative,
    AppContext,
    CompoundRule,
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
    'lowercase_letters': {
        'alpha': 'a', 'bravo': 'b', 'charlie': 'c', 'delta': 'd',
        'echo': 'e', 'foxtrot': 'f', 'golf': 'g', 'hotel': 'h',
        'indigo': 'i', 'juliet': 'j', 'kilo': 'k', 'lima': 'l',
        'mike': 'm', 'november': 'n', 'oscar': 'o', 'poppa': 'p',
        'quiche': 'q', 'romeo': 'r', 'sierra': 's', 'tango': 't',
        'uniform': 'u', 'victor': 'v', 'whiskey': 'w', 'x-ray': 'x',
        'yankee': 'y', 'zulu': 'z'
        },
    'symbols': {
        'left paren': 'lparen',
        'right paren': 'rparen',
        'left bracket': 'lbracket',
        'right bracket': 'rbracket',
        'left brace': 'lbrace',
        'right brace': 'rbrace',
        'quote': 'squote',
        'double quote': 'dquote',
        'backslash': 'backslash',
        'forward slash': 'slash',
        'full stop': 'dot',
        'comma': 'comma',
        },
    'digits': {
        ('dig ' + word): num for word, num in {
            'zero': '0', 'one': '1', 'two': '2', 'three': '3',
            'four': '4', 'five': '5', 'six': '6', 'seven': '7',
            'eight': '8', 'niner': '9'
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
    aenea.vocabulary.uninhibit_global_dynamic_vocabulary(
        GRAMMAR_NAME, GRAMMAR_TAGS
        )
    for tag in GRAMMAR_TAGS:
        aenea.vocabulary.unregister_dynamic_vocabulary(tag)

    global charwise_grammar
    if charwise_grammar:
        charwise_grammar.unload()
    charwise_grammar = None


def setup_key_mappings():
    # See the Dragonfly documentation to see what the values should be:
    # http://dragonfly.readthedocs.io/en/latest/_modules/dragonfly/actions/action_key.html?highlight=lparen
    # Not all symbols are here. Feel free to add the ones you need

    # TODO NEXT USE and test (lower, upper ,symbol, digit)
    # TODO AFTER test vim grammar real time

    CHAR_KEY_MAPPINGS['uppercase_letters'] = {
        UPPERCASE_KEY_PREFIX + speech: 's-' + letter
        for speech, letter in CHAR_KEY_MAPPINGS['lowercase_letters'].iteritems()
        }

    for sub_mappings in {s for s in CHAR_KEY_MAPPINGS.keys() if s != 'all'}:
        CHAR_KEY_MAPPINGS['all'].update(CHAR_KEY_MAPPINGS[sub_mappings])


def setup_grammar():
    vim_context = create_app_context()
    new_grammar = Grammar(GRAMMAR_NAME, context=vim_context)

    # Only use the grammar for vim_context # TODO remove?
    aenea.vocabulary.inhibit_global_dynamic_vocabulary(
        GRAMMAR_NAME, GRAMMAR_TAGS, context=vim_context
        )
    # top_level_rule =
    # aenea.vocabulary.register_dynamic_vocabulary(GRAMMAR_TAGS[0]) #TODO

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

    def value(self, node):
        return Key(MappingRule.value(self, node))


class CharwiseVimRule(CompoundRule):
    """
    The top level rule.

    Allows for saying multiple commands at once, but will end
    after dictating words (see :class:`~TextEntryRule`)
    """
    repeated_rules_key = 'multiple_repeatable_rules'
    spec = '[<{}>]'.format(repeated_rules_key)  # TODO End with TextEntryRule
    _repeatable_rules = [
        # TODO replace with count
        RuleRef(SingleCharRule())
        # TODO add commands
        ]
    extras = [
        Repetition(
            Alternative(_repeatable_rules),
            max=2,
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
