import operator
import re
import datetime

import aenea.config
import aenea.misc
import aenea.vocabulary

from aenea import (
    AlwaysContext,
    Key,
    Text,
    Mouse,
    Pause,
    Function,
)

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

# TODO Split this big file up into smaller files

# TODO Add customisability, especially for different platforms

PRINT_COUNTER_STATISTICS = False

GRAMMAR_NAME = 'charwise_vim'
INHIBITED_GRAMMAR_TAGS = ["vim.insertions", "multiedit.count", "global"]

CHAR_KEY_MAPPINGS = {  # TODO move this into a separate importable file?
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
        # Copied from aenea/client/misc.py (but modified greatly for improved
        # accuracy)
        'share': 'a',
        'bat': 'b',
        'cot': 'c',
        'drum': 'd',
        'each': 'e',
        'fine': 'f',
        'gust': 'g',
        'harp': 'h',
        'site': 'i',
        'jury': 'j',
        'crunch': 'k',
        'look': 'l',
        'made': 'm',
        'need': 'n',
        'odd': 'o',
        'paint': 'p',
        'quest': 'q',
        'red': 'r',
        'sun': 's',
        'trap': 't',
        'urge': 'u',
        'vote': 'v',
        'whale': 'w',
        'plex': 'x',
        'yes': 'y',
        'zeal': 'z'
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
        'left square|lacket': 'lbracket',
        'right square|racket': 'rbracket',
        'left brace|lace': 'lbrace',
        'right brace|race': 'rbrace',
        'less than|left angle|langle': 'langle',
        'greater than|right angle|wrangle': 'rangle',
        # Quotes
        '(single|sing) quote': 'squote',
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
        'ampersand': 'ampersand',
        '(asterisk|aster)': 'asterisk',
        # Spaces
        'space': 'space',
        'tab': 'tab',
        'enter': 'enter',
        # Other
        # 'dot' is too short and does not have a unique vowel sound, so can be
        # easily mistaken for something else by dragon
        'point': 'dot',
        'comma': 'comma',
        'question [mark]': 'question',
        'underscore': 'underscore',
        'dash': 'minus',
        # 'colon' gets confused with 'comma', 'con', or 'con four'.
        'ratio': 'colon',
        'piper': 'bar',
        'equals': 'equal',
        'plus': 'plus',
        'tilde': 'tilde',
        # Note: Semicolon does not exist in dragonfly 0.6.5.
        '(semicolon|semi)': 'semicolon',
    },
    'special-keys': {
        # For tmux, use the 'quit' SimpleCommandRule instead of 'escape'
        # because of the escape button delay bug
        'escape': 'escape',
        '(backspace|delete)': 'backspace',
        'gup': 'up',  # up gets some false positives sometimes
        'down': 'down',
        'left': 'left',
        'right': 'right',
        'page up': 'pgup',
        'page down': 'pgdown',
        'home': 'home',
        'end': 'end',
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
    return aenea.wrappers.AeneaContext(
        AlwaysContext(),
        AppContext(title='VIM'),
    )


class Utils:
    open_spotlight = Key('w-space') + Pause('10')


# Rules


END_CONTINUABLE_TEXT_WORD = 'fan-tar-chee'


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
        'alter': 'a',  # alt doesn't have very good accuracy
        # Command key on Mac / Windows key
        '(windows|command|apple)': 'w',

        # Convenience combinations
        'mash mod': 'csw',
    }


class KeyRepeatRule(MappingRule):
    mapping = {
        'double': 2,
        'triple': 3,
        'quadruple': 4,
        # Do you *really* need any more?
    }


class ModifiableSingleKeyRule(CompoundRule):
    """
    A SingleKeyRule with 0 or more modifier keys, or repeats.

    You can say things like:
    - 'alpha'
    - 'control space'
    - 'command shift alpha'
    """
    spec = '[<repeats>] [<modifiers>] <SingleKeyRule>'
    extras = [
        RuleRef(KeyRepeatRule(), name='repeats'),
        Repetition(
            RuleRef(ModifierKeyRule()),
            max=8,
            name='modifiers',
        ),
        RuleRef(SingleKeyRule(), name='SingleKeyRule'),
    ]

    def value(self, node):
        child_grammar_nodes = node.children[0].children[0]
        # Returns something like [2, ['c', 's'], 'a']
        grammar_values = child_grammar_nodes.value()

        repeats = grammar_values[0] or 1
        modifiers = ''.join(grammar_values[1] or [])
        char = grammar_values[2]

        if modifiers:
            key_str = '{}-{}'.format(modifiers, char)
        else:
            key_str = char

        return Key(key_str) * repeats


def notes_complete_line():
    # Propietary function for my workflow
    Key('w-right,ws-left,w-x,backspace').execute()
    Key('w-down, asterisk, space').execute()

    Text(str(datetime.datetime.now())).execute()
    Key('space, w-v').execute()

    Pause('40').execute()
    Key('w-up').execute()


class SimpleCommandRule(MappingRule):
    """
    Similar to SingleKeyRule, but you can include aliases for key combinations
    and sequences. These are not affected by ModifierKeyRule.
    """

    setup_key_mappings()
    mapping = {
        # Mouse
        'click left': Mouse('left'),
        'click right': Mouse('right'),

        # Vim key aliases
        'align (par|paragraph)': Text('gwip'),
        # Delay for escape because of tmux escape delay bug
        'quit': Key('escape') + Pause('20'),
        'save file': Key('escape,colon,w,enter'),
        'exit': Key('colon,q,enter'),
        'force save': Key('escape,colon,w,exclamation,enter'),
        'save exit': Key('escape,colon,w,q,enter'),
        'save all': Key('escape,colon,w,a,enter'),
        'move line up': Text('ddkP'),
        'move line down': Text('ddp'),
        'change word': Text('ciw'),
        'switch split': Key('c-w,c-w'),

        # Vim tags (or IntelliJ)
        '(jump deaf|jump to definition)': Key('c-rbracket'),
        'jump back': Key('c-t'),

        # IntelliJ (Mac shortcuts - TODO detect platform)
        # TODO move to new file
        'find (action|actions)': Key('ws-a'),
        'find (usages|uses)': Key('a-f7'),
        'find (subclasses|subclass)': Key('wa-b'),
        'find in superclass': Key('w-u'),
        'find in (path|files)': Key('ws-f'),
        'do rename': Key('s-f6'),
        'next error': Key('f2'),
        'previous error': Key('s-f2'),
        'toggle breakpoint': Key('w-f8'),
        'file structure': Key('w-f12'),

        # Mac shortcuts (TODO remove)
        'mac delete line': Key('w-right,ws-left,w-x,backspace'),
        'mac line up': Key(
            'w-right,ws-left,w-x,backspace,w-left,w-v,enter,up,w-right'
        ),
        'mac line down': Key(
            'w-right,ws-left,w-x,backspace,down,w-right,enter,w-v'
        ),
        'mac copy all': Key('w-a,w-c'),
        'mac cut all': Key('w-a,w-x'),
        'notes complete line': Function(notes_complete_line),

        # Windows shortcuts (TODO remove)
        'win copy all': Key('c-a,c-c,right'),
        'win cut all': Key('c-a,c-x,right'),

        # tmux (assumes prefix key is control-s)
        'switch panes': Key('c-s,semicolon,c-s,z'),

        # Vocabulary (TODO Don't copy paste from programming.json)
        'compare equal': Text(' == '),
        'compare not equal': Text(' != '),
        'compare greater': Text(' > '),
        'compare less': Text(' < '),
        'compare greater equal': Text(' >= '),
        'compare less equal': Text(' <= '),
        'boolean or': Text(' || '),
        'boolean and': Text(' && '),
        'bitwise or': Text(' | '),
        'bitwise and': Text(' & '),
        'bitwise ex or': Text(' ^ '),
        'math times': Text(' * '),
        'math divide': Text(' / '),
        'math add': Text(' + '),
        'math minus': Text(' - '),
        'set value': Text(' = '),
        'set plus equal': Text(' += '),
        'set minus equal': Text(' -= '),
        'set times equal': Text(' *= '),
        'set divided equal': Text(' /= '),

        # Programming aliases
        # NOTE: Tried to word these so these are usable for multiple languages
        # Remember that we don't know what language we are using from this
        # grammar.
        # NOTE 2: To avoid collisions with other commands, prefix the short
        # ones with 'key'.
        # NOTE 3: Prefix some actions with 'do' to improve accuracy
        'key class': Text('class'),
        'key fun': Text('fun'),
        'key end': Text('end'),
        'key function': Text('function'),
        'key const': Text('const'),
        'key let': Text('let'),
        'key var': Text('var'),
        'key val': Text('val'),
        'key bool': Text('bool'),
        'key boolean': Text('boolean'),
        'key int': Text('int'),
        'key module': Text('module'),
        'key deaf': Text('def'),
        'key null': Text('null'),
        'key nil': Text('nil'),
        'key for': Text('for'),
        'key while': Text('while'),
        'key if': Text('if'),
        'key else': Text('else'),
        'key do': Text('do'),
        'key when': Text('when'),
        'key case': Text('case'),
        'key conned': Text('cond'),
        'key return': Text('return'),
        'key ee-lif': Text('elif'),
        'key new': Text('new'),
        'key this': Text('this'),
        'key self': Text('self'),
        'key true': Text('true'),
        'key false': Text('false'),
        'key try': Text('try'),
        'key except': Text('except'),
        'key catch': Text('catch'),
        'key finally': Text('finally'),

        # Symbol shortcuts
        'lamb dash': Text(' -> '),
        'lamb eek': Text(' => '),
        'back dash': Text(' <- '),
        'pie opper': Text('|> '),  # sounds like 'pipe operator'
        'slash comment': Text('// '),
        'pie dunder': Text('__'),

        # Temporary (TODO move elsewhere)
        'short cat': Key('ws-space') + Pause('10'),
        'do pause': Pause('40'),
        # Temporary spotlight stuff (TODO move elsewhere)
        'spotlight': Utils.open_spotlight,
        'edit in vim': Key('w-a,w-c,wc-v'),
        'open in new tab': Key('w-c,w-t,w-v,enter'),
        'clipboard': Utils.open_spotlight + Text('clipboard') + Key('enter'),
        'clear notifications':
            Utils.open_spotlight + Text('clear notifications') + Key('enter'),
        'toggle music': Utils.open_spotlight + Text('play') + Key('enter'),
        'jupiter run all': Key('ws-f')
            + Pause('10')
            + Text('restart kernel and run all cells')
            + Key('down,down,enter'),

        # Terms/words that dragon has some difficulty understanding even after
        # manually correcting dragon to train it
        'term to do': Text('TODO: '),
        'term to do next': Text('TODO NEXT: '),
        'term to do after': Text('TODO AFTER: '),
        'term to do sometime': Text('TODO SOMETIME: '),
        'term to do later': Text('TODO LATER: '),
        'term to do last': Text('TODO LAST: '),
        'term whip': Text('WIP '),
        'term tea mucks': Text('tmux'),
        'term vim': Text('vim'),
        'term imple': Text('impl'),
        'term git': Text('git'),
        'term diff': Text('diff'),
        'term grep': Text('grep'),
        'term kotlin': Text('kotlin'),
        # It is difficult to get dragon to not interpret saying 'python' as
        # 'hyphen'
        'term python': Text('python'),
        'term cat': Text('cat'),  # Dragon has difficulty recognising this word
        'term upper jason': Text('JSON'),
        'term jason': Text('json'),
        'term in it': Text('init'),
        'term sync': Text('sync'),
    }


class RepeatLastRule(CompoundRule):
    REPEAT_CHUNK = 'repeat chunk'
    REPEAT_LAST = 'repeat last'
    last_chunk = [Text('')]
    spec = '{}|{}'.format(REPEAT_CHUNK, REPEAT_LAST)

    def value(self, node):
        action = ' '.join(node.words())

        if action == RepeatLastRule.REPEAT_CHUNK:
            return lambda: reduce(operator.add, RepeatLastRule.last_chunk)
        elif action == RepeatLastRule.REPEAT_LAST:
            return lambda: RepeatLastRule.last_chunk[-1]
        else:
            raise ValueError('Invalid action: ' + action)


class TextRule(CompoundRule):
    """
    Text insertion. E.g. saying 'camel my variable name' => types
    'myVariableName'.
    """
    spec = ('[upper | natural] ( proper | camel | relpath | abs-path | score '
            '| sentence | spay-tince | scope-resolve | jumble | dotway '
            '| spineway | natway | spaceway | spayway | snakeway '
            '| brooding-narrative | title | params ) '
            '[<dictation>]')
    extras = [Dictation(name='dictation')]

    def value(self, node):
        words = node.words()
        self.preprocess_words(words)

        uppercase = words[0] == 'upper'
        lowercase = words[0] != 'natural'

        if lowercase:
            words = [word.lower() for word in words]
        if uppercase:
            words = [word.upper() for word in words]

        if words[0].lower() in ('upper', 'natural'):
            del words[0]

        format_type = words[0].lower().replace('-', '')
        del words[0]

        words = self.properly_separate_words(words)

        func = getattr(TextRule, 'format_%s' % format_type)
        formatted = func(words)

        return Text(formatted)

    def properly_separate_words(self, words):
        # Fix dragon not properly formatting words. Examples of `words`:
        # ['hello', 'world'],
        # ["let's", 'use', 'the', 'control panel'],
        # ['well', 'I\\pronoun', 'think', 'we', 'should', 'go'],
        # ['\x96\\dash\\dash'],  # when you say 'natword dash'
        # ['\x97\\em-dash\\m dash'],  # when you say 'natword em dash'
        # ["let's", 'go', 'off-campus'],

        def flat_map(function, iterable):
            map_results = [function(item) for item in iterable]
            if not map_results:
                return []
            return reduce(operator.add, map_results)

        words = [
            word.split('\\', 1)[0].replace('-', '')
            for word in words
            if not re.match(r'^[,\x96\x97]', word)
        ]
        words = flat_map(lambda word: word.split(' '), words)
        words = [word for word in words if word]
        return words

    def preprocess_words(self, words):
        pass

    @staticmethod
    def format_snakeway(text):
        formatted = text[0][0].upper()
        formatted += text[0][1:]
        formatted += ('_' if len(text) > 1 else '')
        formatted += TextRule.format_score(text[1:])
        return formatted

    @staticmethod
    def format_score(text):
        return '_'.join(text)

    @staticmethod
    def format_params(text):
        return ', '.join(text)

    @staticmethod
    def format_camel(text):
        return text[0] + ''.join(
            [word[0].upper() + word[1:]
             for word in text[1:]]
        )

    @staticmethod
    def format_proper(text):
        return ''.join(word.capitalize() for word in text)

    @staticmethod
    def format_relpath(text):
        return '/'.join(text)

    @staticmethod
    def format_abspath(text):
        return '/' + TextRule.format_relpath(text)

    @staticmethod
    def format_scoperesolve(text):
        return '::'.join(text)

    @staticmethod
    def format_jumble(text):
        return ''.join(text)

    @staticmethod
    def format_dotway(text):
        return '.'.join(text)

    @staticmethod
    def format_spineway(text):
        return '-'.join(text)

    @staticmethod
    def format_natway(text):
        return ' '.join(text)

    @staticmethod
    def format_spaceway(text):
        if len(text) == 0:
            return ''
        return ' '.join(text) + ' '

    format_spayway = format_spaceway

    @staticmethod
    def format_broodingnarrative(text):
        return ''

    @staticmethod
    def format_sentence(text):
        if len(text) == 0:
            return ''
        return ' '.join([text[0].capitalize()] + text[1:])

    @staticmethod
    def format_spaytince(text):
        if len(text) == 0:
            return ''
        return ' '.join([text[0].capitalize()] + text[1:]) + ' '

    @staticmethod
    def format_title(text):
        words_to_keep_lowercase = (
            'a,an,the,at,by,for,in,of,on,to,up,and,as,but,or,nor'.split(',')
        )
        words = []
        for index, word in enumerate(text):
            if index == 0 or word not in words_to_keep_lowercase:
                words.append(word.capitalize())
            else:
                words.append(word)

        return ' '.join(words)


class ContinuableTextRule(TextRule):
    spec = TextRule.spec + ' ' + END_CONTINUABLE_TEXT_WORD
    extras = TextRule.extras

    def preprocess_words(self, words):
        words.pop()


class OpenAppRule(CompoundRule):
    """
    Open app with Spotlight/Alfred
    """
    spec = 'open-app <dictation>'
    extras = [Dictation(name='dictation')]

    def value(self, node):
        words = [word.split('\\')[0] for word in node.words()]
        words = ' '.join(words[1:])
        return Utils.open_spotlight + Text(words) + Key('enter')


class Counter:
    EXECUTABLES_BETWEEN_PRINTS = 8
    MAX_RESULTS_TO_PRINT = 10
    counts = dict()
    executable_count = 0

    @staticmethod
    def update(executable):
        string = str(executable)[0:40]
        Counter.executable_count += 1
        if string not in Counter.counts:
            Counter.counts[string] = 1
        else:
            Counter.counts[string] += 1

        Counter.print_stats()

    @staticmethod
    def print_stats():
        if Counter.executable_count % Counter.EXECUTABLES_BETWEEN_PRINTS != 0:
            return
        sorted_counts = sorted(
            Counter.counts.iteritems(),
            key=lambda (k, v): (v, k)
        )
        results_to_print = min(
            Counter.MAX_RESULTS_TO_PRINT,
            len(sorted_counts)
        )

        if not PRINT_COUNTER_STATISTICS:
            return

        print 'Popular executables:'
        for i in reversed(range(-results_to_print, 0)):
            print '  - {}'.format(sorted_counts[i])


class CharwiseVimRule(CompoundRule):
    """
    The top level rule.

    Allows for saying multiple commands at once, but will end after dictating
    words (see :class:`~TextRule`) or some other kind of ending
    rule. (You do not have to say and ending rule).
    """

    spec = '[{}] [<{}>] [<{}>] [<{}>]'.format(
        # Avoid problems with saying END_CONTINUABLE_TEXT_WORD too late
        END_CONTINUABLE_TEXT_WORD,
        'repeated_rules',
        'ending_rules',
        'repeat_last_rule',
    )
    extras = [
        Repetition(
            Alternative([
                RuleRef(ModifiableSingleKeyRule()),
                RuleRef(SimpleCommandRule()),
                RuleRef(ContinuableTextRule()),
            ]),
            max=20,
            name='repeated_rules'
        ),
        Alternative(
            [
                RuleRef(TextRule()),
                RuleRef(OpenAppRule()),
            ],
            name='ending_rules',
        ),
        Repetition(
            RuleRef(RepeatLastRule()),
            name='repeat_last_rule',
            max=20,
        ),
    ]

    def _process_recognition(self, node, extras):
        # NOTE: If node contains a string, but extras contains 'None', then
        # perhaps you have tried to call Key(str) where 'str' is some invalid
        # key name.

        to_execute = extras.get('repeated_rules', [])
        to_execute.append(extras.get('ending_rules'))
        to_repeat_getters = extras.get('repeat_last_rule', [])

        to_execute = [item for item in to_execute if item]

        if to_execute:
            for executable in to_execute:
                print 'Executing {}'.format(executable)
                executable.execute()
                Counter.update(executable)
            RepeatLastRule.last_chunk = to_execute

        # TODO fix can't say 'Something something repeat last' literally
        for to_repeat_getter in to_repeat_getters:
            to_repeat = to_repeat_getter()
            print 'Repeating {}'.format(to_repeat)
            to_repeat.execute()


load()
