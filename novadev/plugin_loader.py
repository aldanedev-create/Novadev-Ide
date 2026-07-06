from __future__ import annotations

"""Plugin metadata loader for NovaDev 1.1.

NovaDev plugins are recorded and documented. Future versions can expand this
file to load package-provided AST nodes, generator hooks, and validation rules.
"""

from dataclasses import dataclass
from typing import List

from .ast_nodes import AppNode, PluginNode, Program


@dataclass
class LoadedPlugin:
    name: str
    status: str = "recorded"


class PluginLoader:
    def collect(self, program: Program) -> List[LoadedPlugin]:
        plugins: List[LoadedPlugin] = []
        for node in program.body:
            if isinstance(node, PluginNode):
                plugins.append(LoadedPlugin(node.name))
            elif isinstance(node, AppNode):
                plugins.extend(LoadedPlugin(plugin.name) for plugin in node.plugins)
        return plugins
