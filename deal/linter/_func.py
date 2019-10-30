import ast
import builtins
import enum
from pathlib import Path
from typing import List

import astroid

from ._extractors import get_name, get_contracts


TEMPLATE = """
contract = PLACEHOLDER
result = contract(*args, **kwargs)
"""


class Category(enum.Enum):
    POST = 'post'
    RAISES = 'raises'
    SILENT = 'silent'


class Func:
    def __init__(self, body: list, args, category: Category):
        self.body = body
        self.args = args
        self.category = category

    @classmethod
    def from_path(cls, path: Path) -> List['Func']:
        text = path.read_text()
        tree = astroid.parse(code=text, path=str(path))
        return cls.from_astroid(tree)

    @classmethod
    def from_text(cls, text: str) -> List['Func']:
        tree = astroid.parse(text)
        return cls.from_astroid(tree)

    @classmethod
    def from_ast(cls, tree: ast.Module) -> List['Func']:
        funcs = []
        for expr in tree.body:
            if not isinstance(expr, ast.FunctionDef):
                continue
            for cat, args in get_contracts(expr.decorator_list):
                funcs.append(cls(
                    body=expr.body,
                    category=Category(cat),
                    args=args,
                ))
        return funcs

    @classmethod
    def from_astroid(cls, tree: astroid.Module) -> List['Func']:
        funcs = []
        for expr in tree.body:
            if not isinstance(expr, astroid.FunctionDef):
                continue
            if not expr.decorators:
                continue
            for cat, args in get_contracts(expr.decorators.nodes):
                funcs.append(cls(
                    body=expr.body,
                    category=Category(cat),
                    args=args,
                ))
        return funcs

    @property
    def contract(self):
        contract = self.args[0]
        # convert astroid node to ast node
        if hasattr(contract, 'as_string'):
            contract = ast.parse(contract.as_string()).body[0].value
        return contract

    @property
    def exceptions(self) -> list:
        excs = []
        for expr in self.args:
            name = get_name(expr)
            if not name:
                continue
            exc = getattr(builtins, name, name)
            excs.append(exc)
        return excs

    @property
    def bytecode(self):
        module = ast.parse(TEMPLATE)
        module.body[0].value = self.contract
        return compile(module, filename='<ast>', mode='exec')

    def run(self, *args, **kwargs):
        globals = dict(args=args, kwargs=kwargs)
        exec(self.bytecode, globals)
        return globals['result']

    def __repr__(self) -> str:
        return '{name}({category}, {contract})'.format(
            name=type(self).__name__,
            contract=ast.dump(self.contract),
            category=self.category.name,
        )
