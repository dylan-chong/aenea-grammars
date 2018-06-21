import aenea.config
import aenea.configuration

from aenea.proxy_contexts import ProxyAppContext

from dragonfly import (
    Alternative,
    AppContext,
    CompoundRule,
    Grammar,
    MappingRule,
    Repetition,
    RuleRef,
)

from aenea import (
    Key,
    Text,
)

# TODO What is aenea.configuration.make_grammar_commands


def load():
    global git_grammar
    context = aenea.wrappers.AeneaContext(
        ProxyAppContext(
            match='regex',
            app_id='(?i)(?:(?:DOS|CMD).*)|(?:.*(?:TERM|SHELL).*)',
        ),
        AppContext(title='git'),
    )
    git_grammar = Grammar('git', context=context)
    git_grammar.add_rule(GitRule())
    git_grammar.load()


def unload():
    global git_grammar
    if git_grammar:
        git_grammar.unload()
    git_grammar = None


class GitCommandRule(CompoundRule):
    def __init__(self, name, options, command_alias=None):
        if command_alias is None:
            command_alias = name

        super(GitCommandRule, self).__init__(
            name=name,
            spec=command_alias + ' <options>',
            extras=[Repetition(
                name='options',
                min=0,
                max=10,
                child=RuleRef(MappingRule(
                    name=name + '_options',
                    mapping=options,
                )),
            )],
        )

    def value(self, node):
        sequence_values = node.children[0].children[0].value()
        option_values = sequence_values[1]

        text = Text(self.name + ' ')
        for option in option_values:
            text += option

        return text


class GitRule(CompoundRule):
    spec = 'git [<command>] [<enter>] [<cancel>]'
    extras = [
        Alternative(name='command', children=[
            RuleRef(name='add', rule=GitCommandRule(
                name='add',
                options={
                    'all': Text('--all '),
                    'dot|point': Text('. '),
                }
            )),
        ]),
        RuleRef(name='enter', rule=MappingRule(
            name='enter',
            mapping={'enter': Key('enter')},
        )),
        RuleRef(name='cancel', rule=MappingRule(
            name='cancel',
            mapping={'cancel': Key('c-c')},
        )),
    ]

    def _process_recognition(self, node, extras):
        print('extras', extras)
        for name, executable in extras.iteritems():
            #              executable.execute()
            print(name, executable)


load()