"""Static analysis of Python source code using the standard `ast` module."""

from __future__ import annotations

import ast
from collections.abc import Iterator

from app.models.parsed import (
    ParameterKind,
    ParsedAttribute,
    ParsedClass,
    ParsedFunction,
    ParsedParameter,
    ParsedSymbol,
)

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef

_SELF_NAMES = frozenset({"self", "cls"})
_NESTED_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


class CodeParseError(ValueError):
    """Raised when the given source code is not valid Python."""

    def __init__(self, message: str, line: int | None = None, offset: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.offset = offset


def parse_source(source: str) -> list[ParsedSymbol]:
    """Extract every class, function and method from the given source code."""
    if not source.strip():
        raise CodeParseError("Source code is empty")

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise CodeParseError(
            f"Invalid Python syntax: {exc.msg}", line=exc.lineno, offset=exc.offset
        ) from exc

    return list(_collect(tree, source, prefix=""))


def _collect(node: ast.Module | ast.ClassDef, source: str, prefix: str) -> Iterator[ParsedSymbol]:
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield _build_function(child, source, prefix)
        elif isinstance(child, ast.ClassDef):
            yield _build_class(child, source, prefix)
            yield from _collect(child, source, f"{prefix}{child.name}.")


def _build_function(node: FunctionNode, source: str, prefix: str) -> ParsedFunction:
    decorators = [ast.unparse(decorator) for decorator in node.decorator_list]
    is_method = bool(prefix)

    return ParsedFunction(
        name=node.name,
        qualified_name=f"{prefix}{node.name}",
        is_async=isinstance(node, ast.AsyncFunctionDef),
        is_method=is_method,
        is_generator=_is_generator(node),
        decorators=decorators,
        parameters=_build_parameters(
            node.args, skip_self=is_method and "staticmethod" not in decorators
        ),
        return_annotation=ast.unparse(node.returns) if node.returns else None,
        returns_value=_returns_value(node),
        raises=_collect_raises(node),
        existing_docstring=ast.get_docstring(node),
        lineno=node.lineno,
        source=ast.get_source_segment(source, node) or "",
    )


def _build_parameters(args: ast.arguments, *, skip_self: bool) -> list[ParsedParameter]:
    positional: list[tuple[ast.arg, ParameterKind]] = [
        (arg, ParameterKind.POSITIONAL_ONLY) for arg in args.posonlyargs
    ]
    positional += [(arg, ParameterKind.POSITIONAL_OR_KEYWORD) for arg in args.args]

    padding: list[ast.expr | None] = [None] * (len(positional) - len(args.defaults))
    defaults = padding + list(args.defaults)

    params: list[ParsedParameter] = []
    for index, ((arg, kind), default) in enumerate(zip(positional, defaults, strict=True)):
        if index == 0 and skip_self and arg.arg in _SELF_NAMES:
            continue
        params.append(_build_parameter(arg, kind, default))

    if args.vararg:
        params.append(_build_parameter(args.vararg, ParameterKind.VAR_POSITIONAL, None))

    for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        params.append(_build_parameter(arg, ParameterKind.KEYWORD_ONLY, default))

    if args.kwarg:
        params.append(_build_parameter(args.kwarg, ParameterKind.VAR_KEYWORD, None))

    return params


def _build_parameter(
    arg: ast.arg, kind: ParameterKind, default: ast.expr | None
) -> ParsedParameter:
    return ParsedParameter(
        name=arg.arg,
        annotation=ast.unparse(arg.annotation) if arg.annotation else None,
        default=ast.unparse(default) if default is not None else None,
        kind=kind,
    )


def _walk_own_scope(node: ast.AST) -> Iterator[ast.AST]:
    """Walk the node's children without descending into nested functions or classes."""
    for child in ast.iter_child_nodes(node):
        if isinstance(child, _NESTED_SCOPES):
            continue
        yield child
        yield from _walk_own_scope(child)


def _is_generator(node: FunctionNode) -> bool:
    return any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in _walk_own_scope(node))


def _returns_value(node: FunctionNode) -> bool:
    return any(isinstance(n, ast.Return) and n.value is not None for n in _walk_own_scope(node))


def _collect_raises(node: FunctionNode) -> list[str]:
    names: list[str] = []
    for child in _walk_own_scope(node):
        if not isinstance(child, ast.Raise) or child.exc is None:
            continue
        exc = child.exc.func if isinstance(child.exc, ast.Call) else child.exc
        name = ast.unparse(exc)
        if name not in names:
            names.append(name)
    return names


def _build_class(node: ast.ClassDef, source: str, prefix: str) -> ParsedClass:
    methods = [
        child.name
        for child in node.body
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not child.name.startswith("_")
    ]

    return ParsedClass(
        name=node.name,
        qualified_name=f"{prefix}{node.name}",
        bases=[ast.unparse(base) for base in node.bases],
        decorators=[ast.unparse(decorator) for decorator in node.decorator_list],
        attributes=_build_attributes(node),
        method_names=methods,
        existing_docstring=ast.get_docstring(node),
        lineno=node.lineno,
        source=ast.get_source_segment(source, node) or "",
    )


def _build_attributes(node: ast.ClassDef) -> list[ParsedAttribute]:
    attributes: dict[str, ParsedAttribute] = {}

    for child in node.body:
        if isinstance(child, ast.AnnAssign) and isinstance(child.target, ast.Name):
            _add_attribute(attributes, child.target.id, child.annotation, child.value)
        elif isinstance(child, ast.Assign):
            for target in child.targets:
                if isinstance(target, ast.Name):
                    _add_attribute(attributes, target.id, None, child.value)

    init = next(
        (
            child
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name == "__init__"
        ),
        None,
    )
    if init is not None:
        for child in _walk_own_scope(init):
            if isinstance(child, ast.AnnAssign) and _is_self_attribute(child.target):
                _add_attribute(attributes, child.target.attr, child.annotation, None)
            elif isinstance(child, ast.Assign):
                for target in child.targets:
                    if _is_self_attribute(target):
                        _add_attribute(attributes, target.attr, None, None)

    return list(attributes.values())


def _add_attribute(
    attributes: dict[str, ParsedAttribute],
    name: str,
    annotation: ast.expr | None,
    default: ast.expr | None,
) -> None:
    if name.startswith("_"):
        return

    unparsed = ast.unparse(annotation) if annotation is not None else None
    existing = attributes.get(name)
    if existing is None:
        attributes[name] = ParsedAttribute(
            name=name,
            annotation=unparsed,
            default=ast.unparse(default) if default is not None else None,
        )
    elif existing.annotation is None and unparsed is not None:
        existing.annotation = unparsed


def _is_self_attribute(node: ast.expr) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )
