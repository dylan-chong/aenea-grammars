import aenea.config
import aenea.misc
import aenea.vocabulary

from aenea import (
    Key,
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
    #
    # Put any alternative sayings here (e.g. you could say 'indie' instead of
    # 'indigo' to press 'i'). If you need to press modifier keys, then add to
    # SimpleCommandRule.
    #
    # NOTE: Not all symbols are here. Feel free to add the ones you need

    # In each sub-dict: What to say (key): String to pass into Key(str) (value)
    'all': {},  # All mappings excluding modifier keys. Updated below
    'letters': {
        # Copied from aenea/client/misc.py
        'alpha': 'a',
        'bravo': 'b',
        'charlie': 'c',
        'delta': 'd',
        'echo': 'e',
        'fox': 'f',
        'golf': 'g',
        'hotel': 'h',
        '(indigo|indie)': 'i',
        '(juliet|julie)': 'j',
        'kilo': 'k',
        'lima': 'l',
        'mike': 'm',
        '(november|neighbour)': 'n',
        'oscar': 'o',
        'poppy': 'p',  # Different from 'poppa' (avoids conflict with 'proper')
        'quiche': 'q',
        'romeo': 'r',
        'sierra': 's',
        'tango': 't',
        '(uniform|unit)': 'u',
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
        '(left (paren|parenthesis)|push)': 'lparen',
        '(right (paren|parenthesis)|pop)': 'rparen',
        # saying 'left bracket' makes Dragon type '('
        'left square|leer': 'lbracket',
        'right square|rear': 'rbracket',
        'left brace|lace': 'lbrace',
        'right brace|race': 'rbrace',
        'less than|left angle|langle': 'langle',
        'greater than|right angle|wrangle': 'rangle',
        # Quotes
        '([single] quote|smote)': 'squote',
        '(double|dub) quote': 'dquote',
        'backtick': 'backtick',
        # Slashes
        'backslash': 'backslash',
        '[forward] slash': 'slash',
        # Shift + Keys 1-8
        '(exclamation [mark]|bang)': 'exclamation',
        'at sign': 'at',
        'hash': 'hash',
        'dollar': 'dollar',
        'percent': 'percent',
        'caret': 'caret',
        '(ampersand|amp)': 'ampersand',
        '(asterisk|star)': 'asterisk',
        # Spaces
        '(space [bar] | spay)': 'space',
        'tab': 'tab',
        '(enter|new line)': 'enter',
        # Other
        '(full stop|dot)': 'dot',
        'comma': 'comma',
        '(question [mark]|quest)': 'question',
        '(underscore|rail)': 'underscore',
        '(dash)': 'minus',
        'colon': 'colon',
        '(piper|vertical bar)': 'bar',
        '(equals|equal)': 'equal',
        'plus': 'plus',
        'tilde': 'tilde',
        # Semicolon does not exist in dragonfly 0.6.5.
        # There is a SimpleCommandRule to get around this
    },
    'special-keys': {
        '(escape|quit)': 'escape',
        '(backspace|chuck)': 'backspace',
        'up': 'up',
        'down': 'down',
        'left': 'left',
        'right': 'right',
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
            # Both title and app_id of the active app/window must match for
            # this grammar to be active
            match='regex',
            title='(?i).*(?:VIM|' + terminal_window_names + ').*' +
                  '|(?:' + intellij_window_title +
                  '|' + blank_window_title + ')',
            app_id='(?i).*VIM.*|.*TERM.*|' + intellij_app_name,
        ),
        AppContext(title='VIM')
    )


# Random Helpers


def text_to_key_str(text):
    """
    Splits the text (e.g. 'abc') into comma-separated characters suitable for
    use in the Key constructor.

    It currently only works with lowercase letters, digits, and spaces
    """
    return ','.join(text).replace(' ', 'space')


# Rules


class SingleKeyRule(MappingRule):
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
        # Command key on Mac. (Remember, it's 'w' for command, not 'c'!)
        '(windows|command)': 'w',
    }


class ModifiableSingleKeyRule(CompoundRule):
    """
    A SingleKeyRule with 0 or more modifier keys.

    You can say things like:
    - 'alpha'
    - 'control space'
    - 'command shift alpha'
    """
    spec = '[<modifiers>] <SingleKeyRule>'
    extras = [
        Repetition(
            RuleRef(ModifierKeyRule()),
            max=8,
            name='modifiers',
        ),
        RuleRef(SingleKeyRule(), name='SingleKeyRule'),
    ]

    def value(self, node):
        # Seriously, what kind of api makes you write this sort of nonsense?
        child_grammar_nodes = node.children[0].children[0]
        grammar_values = child_grammar_nodes.value()  # e.g. [['c', 's'], 'a']

        modifiers = ''.join(grammar_values[0] or [])
        char = grammar_values[1]

        if modifiers:
            key_str = '{}-{}'.format(modifiers, char)
        else:
            key_str = char

        return Key(key_str)


class SimpleCommandRule(MappingRule):
    """
    Similar to SingleKeyRule, but you can include aliases for key combinations
    and sequences. These are not affected by ModifierKeyRule.
    """

    setup_key_mappings()
    mapping = {
        # Gets around invalid Key('semicolon') error
        '(semicolon|semi)': Text(';'),

        # Vim key aliases
        '(page up)': Key('c-u'),
        '(page down)': Key('c-d'),
        'delete line': Text('dd'),
        'align (par|paragraph)': Text('mzgqip`z'),
        'yank (file|all)': Text('mzggVGy`z'),
        'save file': Key('colon,w,enter'),
        'save and quit': Key('colon,w,q,enter'),
        'save all [files]': Key('colon,w,a,enter'),
        'save all [files] and quit': Key('colon,w,q,enter'),
        'move line up': Text('ddkP'),
        'move line down': Text('ddp'),
        'change word': Text('ciw'),
        'switch split': Key('c-w,c-w'),

        # Vim tags (or IntelliJ)
        '(jump deaf|jump to definition)': Key('c-rbracket'),
        'jump back': Key('c-t'),

        # IntelliJ (Mac shortcuts - TODO detect platform)
        'find (action|actions)': Key('ws-a'),
        '(refactor|rename)': Key('s-f6'),
        'find (usages|uses)': Key('a-f7'),
        'find (subclasses|subclass)': Key('wa-b'),
        'find in superclass': Key('w-u'),
        'find in (path|files)': Key('ws-f'),
        '(open|find) class': Key('w-o'),
        '(open|find) symbol': Key('wa-o'),
        'recent files': Key('w-e'),
        'search files': Key('shift:down, shift:up, shift:down, shift:up'),
        'next error': Key('f2'),
        'previous error': Key('s-f2'),
        'toggle breakpoint': Key('w-f8'),
        'file structure': Key('w-f12'),

        # Custom IntelliJ shortcuts (Mac)
        # A lot of these are remapped to avoid conflicting with (IDEA) Vim
        # shortcuts
        'run configuration': Key('csw-r'),
        'debug configuration': Key('csw-d'),
        'edit (configuration|configurations)': Key('csw-e'),

        # Vocabulary (TODO Don't copy paste from programming.json)
        'assign': Text(' = '),
        'compare eek': Text(' == '),
        'compare not eek': Text(' != '),
        'compare (greater|great)': Text(' > '),
        'compare less': Text(' < '),
        'compare (greater|great) eek': Text(' >= '),
        'compare less eek': Text(' <= '),
        'boolean ore': Text(' || '),
        'boolean and': Text(' && '),
        'bit ore': Text(' | '),
        'bit and': Text(' & '),
        'bit ex or': Text(' ^ '),
        'times': Text(' * '),
        'divide': Text(' / '),
        'add': Text(' + '),
        '(minus|take away)': Text(' - '),
        'assign (plus|add) eek': Text(' += '),
        'assign minus eek': Text(' -= '),
        'assign times eek': Text(' *= '),
        'assign divided eek': Text(' /= '),
        'assign mod eek': Text(' %%= '),

        # Programming aliases
        # NOTE: Tried to word these so these are usable for multiple languages
        # Remember that we don't know what language we are using from this
        # grammar.
        # NOTE 2: If a keyword is specific to a limited number of languages,
        # and is only a single syllable, then to avoid accidental stuff, prefix
        # the command with 'key'.
        'key class': Text('class'),
        'key let': Text('let '),
        'key var': Text('var'),
        'key deaf': Text('def '),
        'key deaf pee': Text('defp '),
        'return': Text('return'),
        'if': Text('if '),
        'else': Text('else '),
        'ee-lif': Text('elif '),
        'new': Text('new'),
        'lamb dash': Text(' -> '),
        'lamb eek': Text(' => '),
        'slash comment': Text('// '),
        'pie opper': Text('|> '),  # sounds like 'pipe operator'
        # assumes editor types '}' automatically
        '(bee|brace) block': Key('space,lbrace,enter'),
        'slash doc comment': Key('slash,asterisk,asterisk,enter'),

        # Temporary
        'short cat': Key('ws-space'),
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


def format_params(text):
    return ', '.join(text)


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

format_naewid = format_natword

def format_spaceword(text):
    return ' '.join(text) + ' '


format_spaywid = format_spaceword


def format_broodingnarrative(text):
    return ''


def format_sentence(text):
    return ' '.join([text[0].capitalize()] + text[1:])


def format_title(text):
    return ' '.join([word[0].upper() + word[1:] for word in text])


# TODO copy changes to vim grammar
class IdentifierInsertion(CompoundRule):
    """
    Text insertion. E.g. saying 'camel my variable name' => types
    'myVariableName'.
    """
    spec = ('[upper | natural] ( proper | camel | rel-path | abs-path | score '
            '| sentence | scope-resolve | jumble | dotword | dashword '
            '| natword | naewid | spaceword | spaywid | snakeword '
            '| brooding-narrative | title | params ) '
            '[<dictation>]')
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
        RuleRef(ModifiableSingleKeyRule()),
        RuleRef(SimpleCommandRule()),
    ]

    spec = '[<{}>] [<{}>]'.format(_repeated_rules_key,
                                  _identifier_insertion_key)
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

        # Press keys / enter text for what user just said

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
