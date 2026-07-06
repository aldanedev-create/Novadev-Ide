from __future__ import annotations

"""Recursive-descent parser for NovaDev 1.1.

The parser consumes lexer tokens and creates AST nodes. It understands both the
full-stack NovaDev declarations (`app`, `table`, `page`, `route`, `theme`) and a
small dynamic programming language (`let`, `print`, `if`, `while`, `function`).
"""

from typing import Any, Iterable, List, Optional

from .ast_nodes import (
    AppNode,
    ArchitectureNode,
    AssignNode,
    AuthNode,
    BinaryOpNode,
    BreakNode,
    CallNode,
    ClassNode,
    ComponentNode,
    ContinueNode,
    FileNode,
    FilesystemNode,
    FieldNode,
    FolderNode,
    ForNode,
    FunctionNode,
    GeneratorNode,
    IdentifierNode,
    IfNode,
    ImportNode,
    ExportNode,
    IgnoreNode,
    IndexNode,
    LetNode,
    ListNode,
    LiteralNode,
    ModuleNode,
    ObjectNode,
    PageNode,
    PrintNode,
    Program,
    PluginNode,
    ResourceNode,
    ReturnNode,
    RouteNode,
    TableNode,
    TemplateNode,
    ThemeNode,
    TryCatchNode,
    TupleNode,
    UnaryOpNode,
    UseNode,
    WhileNode,
    WorkflowNode,
    CustomCodeNode,
    SourceFileNode,
)
from .lexer import Lexer, Token


class NovaSyntaxError(Exception):
    def __init__(self, message: str, token: Optional[Token] = None):
        if token:
            super().__init__(f"{message} at line {token.line}, column {token.column}")
        else:
            super().__init__(message)
        self.token = token


NAME_TOKENS = {
    "IDENTIFIER",
    "APP",
    "THEME",
    "USE",
    "IMPORT",
    "EXPORT",
    "AS",
    "DEFAULT",
    "PLUGIN",
    "WORKFLOW",
    "INPUT",
    "CREATES",
    "CLEARS",
    "VALIDATES",
    "NOTIFY",
    "USES",
    "USING",
    "SHOWS",
    "MODULE",
    "SECTION",
    "FROM",
    "HERO",
    "SUBTITLE",
    "ACTION",
    "ESTIMATOR",
    "PYTHON",
    "JS",
    "JAVASCRIPT",
    "CSS",
    "SQL",
    "CUSTOM",
    "ALLOW",
    "UNSAFE_PYTHON",
    "MODE",
    "EXTENDS",
    "SERVICE",
    "UTILITY",
    "VALIDATOR",
    "MIDDLEWARE",
    "POLICY",
    "TABLE",
    "PAGE",
    "ROUTE",
    "AUTH",
    "REQUIRE",
    "ROLE",
    "RETURN",
    "BREAK",
    "CONTINUE",
    "FORM",
    "CHART",
    "CARD",
    "MODAL",
    "NAVBAR",
    "SIDEBAR",
    "LINK",
    "TO",
    "COLUMNS",
    "ACTIONS",
    "FIELDS",
    "SUBMIT",
    "VALUE",
    "TYPE",
    "TEXT",
    "BUTTON",
    "IF",
    "ELIF",
    "ELSE",
    "WHILE",
    "FOR",
    "IN",
    "FUNCTION",
    "CLASS",
    "TRY",
    "CATCH",
    "LET",
    "PRINT",
    "FILESYSTEM",
    "DISCOVER",
    "FOLDER",
    "FILE",
    "TEMPLATE",
    "RESOURCES",
    "ASSETS",
    "IGNORE",
    "LANGUAGE",
    "DESCRIPTION",
    "GENERATE",
    "PROJECT",
    "STACK",
    "DATABASE",
    "LAYOUT",
    "COMPONENT",
    "REPEAT",
    "GENERATOR",
    "FRONTEND",
    "BACKEND",
    "AUTHENTICATION",
    "STRUCTURE",
    "DOCS",
    "CUSTOMIZE",
    "ARCHITECTURE",
    "MOVE",
    "CREATE",
    "DELETE",
    "HTML",
}


DECLARATION_TYPES = (TableNode, PageNode, RouteNode, ThemeNode, AuthNode)


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        body: List[Any] = []
        app: Optional[AppNode] = None

        while not self.at_end():
            self.skip_newlines()
            if self.at_end():
                break
            node = self.statement()
            body.append(node)
            if isinstance(node, AppNode):
                app = node

        if app is None:
            declarations = [node for node in body if isinstance(node, DECLARATION_TYPES) or self.is_use_theme(node)]
            if declarations:
                app = AppNode("NovaDevApp")
                for node in declarations:
                    app.add_member(node)

        return Program(body=body, app=app)

    def statement(self) -> Any:
        self.skip_newlines()
        if self.match("APP"):
            return self.app_declaration()
        if self.match("TABLE"):
            return self.table_declaration()
        if self.match("PAGE"):
            return self.page_declaration()
        if self.match("ROUTE"):
            return self.route_declaration()
        if self.match("THEME"):
            return self.theme_declaration()
        if self.match("AUTH"):
            return self.auth_declaration()
        if self.match("USE"):
            return self.use_declaration()
        if self.match("IMPORT"):
            return self.import_declaration()
        if self.match("EXPORT"):
            return self.export_declaration()
        if self.match("PLUGIN"):
            return self.plugin_declaration()
        if self.match("WORKFLOW"):
            return self.workflow_declaration()
        if self.match("MODULE"):
            return self.module_declaration()
        if self.match("PYTHON"):
            return self.code_declaration("python")
        if self.match("JS"):
            return self.code_declaration("js")
        if self.match("JAVASCRIPT"):
            return self.code_declaration("js")
        if self.match("CSS"):
            return self.code_declaration("css")
        if self.match("SQL"):
            return self.code_declaration("sql")
        if self.match("CUSTOM"):
            return self.custom_declaration()
        if self.match("ALLOW"):
            return self.allow_declaration()
        if self.match("FILESYSTEM"):
            return self.filesystem_declaration()
        if self.match("DISCOVER"):
            name = self.consume_path_name("Expected folder or module name after 'discover'")
            self.consume_statement_end()
            return ComponentNode("discover", name=name)
        if self.match("STACK"):
            name = self.consume_word("Expected stack name after 'stack'")
            self.consume_statement_end()
            return ComponentNode("stack", name=name)
        if self.match("FRONTEND"):
            name = self.consume_word("Expected frontend target after 'frontend'")
            self.consume_statement_end()
            return ComponentNode("frontend", name=name)
        if self.match("BACKEND"):
            name = self.consume_word("Expected backend target after 'backend'")
            self.consume_statement_end()
            return ComponentNode("backend", name=name)
        if self.match("DATABASE"):
            name = self.consume_word("Expected database name after 'database'")
            self.consume_statement_end()
            return ComponentNode("database", name=name)
        if self.match("STRUCTURE"):
            name = self.consume_word("Expected structure name after 'structure'")
            self.consume_statement_end()
            return ComponentNode("structure", name=name)
        if self.check_value("styling"):
            self.advance()
            name = self.consume_word("Expected styling target after 'styling'")
            self.consume_statement_end()
            return ComponentNode("styling", name=name)
        if self.match("ASSETS"):
            name = self.consume_word("Expected assets setting after 'assets'")
            self.consume_statement_end()
            return ComponentNode("assets", name=name)
        if self.match("DOCS"):
            name = self.consume_word("Expected docs setting after 'docs'")
            self.consume_statement_end()
            return ComponentNode("docs", name=name)
        if self.match("MODE"):
            name = self.consume_word("Expected project mode after 'mode'")
            self.consume_statement_end()
            return ComponentNode("mode", name=name)
        if self.match("PROJECT"):
            return self.project_declaration()
        if self.match("GENERATOR"):
            return self.generator_declaration()
        if self.match("CLASS"):
            return self.class_declaration()
        if self.match("FUNCTION"):
            return self.function_declaration()
        if self.match("LET"):
            return self.let_statement()
        if self.match("PRINT"):
            return self.print_statement()
        if self.match("IF"):
            return self.if_statement()
        if self.match("WHILE"):
            return self.while_statement()
        if self.match("FOR"):
            return self.for_statement()
        if self.match("TRY"):
            return self.try_catch_statement()
        if self.match("RETURN"):
            return self.return_statement()
        if self.match("BREAK"):
            self.consume_statement_end()
            return BreakNode()
        if self.match("CONTINUE"):
            self.consume_statement_end()
            return ContinueNode()
        if self.is_assignment_start():
            return self.assignment_statement()

        expression = self.expression()
        self.consume_statement_end()
        return expression

    def app_declaration(self) -> AppNode:
        name = self.consume_word("Expected app name after 'app'")
        app = AppNode(name)
        self.consume("LBRACE", "Expected '{' after app name")

        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            member = self.statement()
            app.add_member(member)

        self.consume("RBRACE", "Expected '}' to close app block")
        self.consume_statement_end()
        return app

    def table_declaration(self) -> TableNode:
        name = self.consume_word("Expected table name after 'table'")
        table = TableNode(name)
        self.consume("LBRACE", "Expected '{' after table name")

        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            field_name = self.consume_word("Expected field name in table")
            field_type = self.consume_word("Expected field type after field name")
            attributes = self.name_list_until_line_or_brace()
            table.fields.append(FieldNode(field_name, field_type, attributes))
            self.consume_statement_end()

        self.consume("RBRACE", "Expected '}' to close table block")
        self.consume_statement_end()
        return table

    def theme_declaration(self) -> ThemeNode:
        name = self.consume_word("Expected theme name after 'theme'")
        theme = ThemeNode(name)
        self.consume("LBRACE", "Expected '{' after theme name")

        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            key = self.consume_word("Expected theme property name")
            value = self.expression()
            theme.values[key] = value.value if isinstance(value, LiteralNode) else value
            self.consume_statement_end()

        self.consume("RBRACE", "Expected '}' to close theme block")
        self.consume_statement_end()
        return theme

    def auth_declaration(self) -> AuthNode:
        table_name = self.consume_word("Expected auth table name")
        self.consume_statement_end()
        return AuthNode(table_name)

    def use_declaration(self) -> ComponentNode:
        kind = self.consume_dotted_name("Expected what to use, like: use theme CyberDark or use Nova.math")
        if kind != "theme":
            self.consume_statement_end()
            return UseNode(kind)
        theme_name = self.consume_word("Expected theme name after 'use theme'")
        self.consume_statement_end()
        return ComponentNode("use_theme", name=theme_name)

    def import_declaration(self) -> ImportNode:
        if self.match("STRING"):
            module_name = self.previous().value
            alias = ""
            if self.match("AS"):
                alias = self.consume_word("Expected alias after 'as'")
            self.consume_statement_end()
            return ImportNode(
                module_name,
                alias=alias,
                package=module_name.startswith("@nova/"),
                remote=module_name.startswith("http://") or module_name.startswith("https://"),
            )

        module_name, namespace = self.consume_import_path("Expected module name after 'import'")
        alias = ""
        if self.match("AS"):
            alias = self.consume_word("Expected import alias")
        self.consume_statement_end()
        return ImportNode(module_name, alias=alias, namespace=namespace)

    def export_declaration(self):
        is_default = self.match("DEFAULT")
        name = self.consume_word("Expected export name")
        self.consume_statement_end()
        return ExportNode(name, is_default=is_default)

    def plugin_declaration(self) -> PluginNode:
        if self.match("STRING"):
            name = self.previous().value
        else:
            name = self.consume_dotted_name("Expected plugin name")
        self.consume_statement_end()
        return PluginNode(name)

    def workflow_declaration(self) -> WorkflowNode:
        name = self.consume_word("Expected workflow name")
        steps: List[ComponentNode] = []
        self.consume("LBRACE", "Expected '{' after workflow name")
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            if self.match("INPUT"):
                steps.append(ComponentNode("input", name=self.consume_word("Expected input entity")))
            elif self.match("CREATES"):
                steps.append(ComponentNode("creates", name=self.consume_word("Expected created entity")))
            elif self.match("CLEARS"):
                steps.append(ComponentNode("clears", name=self.consume_word("Expected cleared entity")))
            elif self.match("VALIDATES"):
                steps.append(ComponentNode("validates", name=self.consume_dotted_name("Expected validation target")))
            elif self.match("USES"):
                steps.append(ComponentNode("uses", name=self.consume_dotted_name("Expected module.function after uses")))
            elif self.match("NOTIFY"):
                steps.append(ComponentNode("notify", name=self.consume_word("Expected notify target")))
            elif self.match("SHOWS"):
                steps.append(ComponentNode("shows", name=self.consume_word("Expected field after shows")))
            elif self.match("FORM"):
                steps.append(ComponentNode("form", name=self.consume_word("Expected form entity")))
            elif self.check_value("estimate"):
                self.advance()
                if self.match("USING"):
                    steps.append(ComponentNode("uses", name=self.consume_dotted_name("Expected estimator module after using")))
                else:
                    steps.append(ComponentNode("estimate", name=self.consume_dotted_name("Expected estimator name")))
            else:
                key = self.consume_word("Expected workflow step")
                value = ""
                if not self.check("NEWLINE") and not self.check("RBRACE") and not self.check("EOF"):
                    value = self.consume_dotted_name(f"Expected value after workflow {key}")
                steps.append(ComponentNode(key, name=value))
            self.consume_statement_end()
        self.consume("RBRACE", "Expected '}' to close workflow")
        self.consume_statement_end()
        return WorkflowNode(name, steps)

    def module_declaration(self) -> ModuleNode:
        name = self.consume_word("Expected module name")
        language = ""
        if self.check_any({"PYTHON", "JS", "JAVASCRIPT", "CSS", "SQL", "IDENTIFIER"}):
            if not self.check("LBRACE"):
                language = str(self.advance().value).lower()
                if language == "javascript":
                    language = "js"
        exports: List[str] = []
        body: List[Any] = []
        code = ""
        self.consume("LBRACE", "Expected '{' after module declaration")
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            if self.match("EXPORT"):
                exports.append(self.consume_word("Expected exported function or value name"))
                self.consume_statement_end()
            elif self.match("PYTHON"):
                block = self.code_declaration("python")
                language = language or "python"
                code = block.code
                body.append(block)
            elif self.match("JS") or self.match("JAVASCRIPT"):
                block = self.code_declaration("js")
                language = language or "js"
                code = block.code
                body.append(block)
            elif self.match("CSS"):
                block = self.code_declaration("css")
                language = language or "css"
                code = block.code
                body.append(block)
            elif self.match("SQL"):
                block = self.code_declaration("sql")
                language = language or "sql"
                code = block.code
                body.append(block)
            else:
                body.append(self.statement())
        self.consume("RBRACE", "Expected '}' to close module")
        self.consume_statement_end()
        return ModuleNode(name=name, language=language, code=code, exports=exports, body=body)

    def allow_declaration(self) -> ComponentNode:
        setting = self.consume_word("Expected setting after 'allow'")
        value = True
        if not self.check("NEWLINE") and not self.check("RBRACE") and not self.check("EOF"):
            expr = self.expression()
            value = expr.value if isinstance(expr, LiteralNode) else bool(expr)
        self.consume_statement_end()
        return ComponentNode("allow", name=setting, props={"value": value})

    def code_declaration(self, language: str, target: str = "") -> CustomCodeNode:
        if self.match("STRING"):
            code = self.previous().value
            self.consume_statement_end()
            return CustomCodeNode(language=language, code=code, target=target)
        self.consume("LBRACE", f"Expected '{{' or string after {language}")
        code = self.raw_block_source()
        self.consume_statement_end()
        return CustomCodeNode(language=language, code=code, target=target)

    def custom_declaration(self) -> CustomCodeNode:
        target = self.consume_word("Expected custom target, like backend, frontend, css")
        name = ""
        if not self.check("LBRACE"):
            name = self.consume_word("Expected custom block name or '{'")
        self.consume("LBRACE", f"Expected '{{' after custom {target}")
        self.skip_newlines()
        if target in {"css", "sql"} and self.match("STRING"):
            code = self.previous().value
            self.skip_newlines()
            self.consume("RBRACE", f"Expected '}}' after custom {target}")
            self.consume_statement_end()
            return CustomCodeNode(language=target, code=code, target=target, name=name)
        if self.match("PYTHON"):
            node = self.code_declaration("python", target)
        elif self.match("JS") or self.match("JAVASCRIPT"):
            node = self.code_declaration("js", target)
        elif self.match("CSS"):
            node = self.code_declaration("css", target)
        elif self.match("SQL"):
            node = self.code_declaration("sql", target)
        elif self.match("STRING"):
            node = CustomCodeNode(language=target, code=self.previous().value, target=target, name=name)
            self.consume_statement_end()
        else:
            raise NovaSyntaxError("Custom blocks need python, js, css, sql, or a string", self.peek())
        self.skip_newlines()
        self.consume("RBRACE", f"Expected '}}' after custom {target}")
        self.consume_statement_end()
        node.name = name
        return node

    def project_declaration(self) -> Any:
        if self.match("LBRACE"):
            props: dict[str, str] = {}
            customizations: list[Any] = []
            while not self.check("RBRACE") and not self.at_end():
                self.skip_newlines()
                if self.check("RBRACE"):
                    break
                key = self.consume_word("Expected project setting")
                if key == "customize":
                    customizations.extend(self.customize_block())
                    continue
                if key == "architecture":
                    customizations.append(self.architecture_block())
                    continue
                if key in {"folder", "file", "python", "javascript", "js", "css", "html", "sql"}:
                    customizations.append(self.architecture_entry_from_key(key))
                    continue
                if key == "use":
                    props["structure"] = self.consume_word("Expected generator or structure name after project use")
                    self.consume_statement_end()
                    continue
                value = self.consume_word(f"Expected value after project {key}")
                props[key] = value
                self.consume_statement_end()
            self.consume("RBRACE", "Expected '}' to close project block")
            self.consume_statement_end()
            return ComponentNode("project_settings", props=props, children=customizations)

        name = self.consume_word("Expected project name after 'project'")
        if self.match("LBRACE"):
            body: List[Any] = []
            while not self.check("RBRACE") and not self.at_end():
                self.skip_newlines()
                if self.check("RBRACE"):
                    break
                body.append(self.statement())
            self.consume("RBRACE", "Expected '}' to close project block")
            self.consume_statement_end()
            return ComponentNode("project", name=name, children=body)
        self.consume_statement_end()
        return ComponentNode("project_type", name=name)

    def architecture_block(self) -> ArchitectureNode:
        self.consume("LBRACE", "Expected '{' after architecture")
        entries: list[Any] = []
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            key = self.consume_word("Expected architecture entry")
            entries.append(self.architecture_entry_from_key(key))
        self.consume("RBRACE", "Expected '}' to close architecture block")
        self.consume_statement_end()
        return ArchitectureNode(entries)

    def architecture_entry_from_key(self, key: str) -> Any:
        if key == "folder":
            name = self.consume_path_name("Expected folder path")
            self.consume_statement_end()
            return FolderNode(name)
        if key == "file":
            node = self.file_node()
            return node
        if key in {"python", "javascript", "js", "css", "html", "sql"}:
            language = "js" if key == "javascript" else key
            name = self.consume_path_name(f"Expected {language} file path")
            content = ""
            if self.match("LBRACE"):
                self.skip_newlines()
                if self.match("STRING"):
                    content = self.previous().value
                    self.skip_newlines()
                self.consume("RBRACE", f"Expected '}}' to close {language} source file")
            self.consume_statement_end()
            return SourceFileNode(language, name, content)
        raise NovaSyntaxError("Architecture supports folder, file, python, js, css, html, sql", self.previous())

    def customize_block(self) -> list[Any]:
        entries: list[Any] = []
        self.consume("LBRACE", "Expected '{' after customize")
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            action = self.consume_word("Expected customize action")
            if action == "move":
                source = self.consume_title_value("Expected source folder after move")
                if self.match("MINUS"):
                    self.consume("GREATER", "Expected '>' after '-' in move arrow")
                target = self.consume_title_value("Expected target folder after move")
                entries.append(ComponentNode("move", name=source, props={"target": target}))
            elif action in {"create", "delete"}:
                name = self.consume_title_value(f"Expected folder after {action}")
                entries.append(ComponentNode(action, name=name))
            else:
                raise NovaSyntaxError("Customize supports move, create, and delete", self.previous())
            self.consume_statement_end()
        self.consume("RBRACE", "Expected '}' to close customize block")
        self.consume_statement_end()
        return entries

    def generator_declaration(self) -> GeneratorNode:
        generator = GeneratorNode()
        self.consume("LBRACE", "Expected '{' after generator")
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            key = self.consume_word("Expected generator property")
            value = self.consume_word(f"Expected value after generator {key}")
            if key in {"frontend", "backend", "database", "authentication"}:
                setattr(generator, key, value)
            else:
                raise NovaSyntaxError("Generator supports frontend, backend, database, authentication", self.previous())
            self.consume_statement_end()
        self.consume("RBRACE", "Expected '}' to close generator")
        self.consume_statement_end()
        return generator

    def route_declaration(self) -> RouteNode:
        method = self.consume_word("Expected HTTP method after 'route'").upper()
        path_token = self.consume("STRING", 'Expected route path string, like "/api/products"')
        route = RouteNode(method=method, path=path_token.value)
        self.consume("LBRACE", "Expected '{' after route path")

        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            if self.match("REQUIRE"):
                self.apply_require(route)
                self.consume_statement_end()
            elif self.match("RETURN"):
                node = self.return_statement(already_matched=True)
                route.return_expr = node.expression
                route.body.append(node)
            else:
                route.body.append(self.statement())

        self.consume("RBRACE", "Expected '}' to close route block")
        self.consume_statement_end()
        return route

    def page_declaration(self) -> PageNode:
        name = self.consume_word("Expected page name after 'page'")
        page = PageNode(name=name, title=name)
        self.consume("LBRACE", "Expected '{' after page name")

        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            item = self.page_item(page)
            if isinstance(item, ComponentNode):
                page.components.append(item)
            page.body.append(item)

        self.consume("RBRACE", "Expected '}' to close page block")
        self.consume_statement_end()
        return page

    def page_item(self, page: PageNode) -> Any:
        if self.match("REQUIRE"):
            self.apply_require(page)
            self.consume_statement_end()
            return ComponentNode("require", props={"auth": page.requires_auth, "role": page.required_role})
        if self.check_value("title"):
            self.advance()
            title = self.consume_title_value("Expected quoted title after title")
            self.consume_statement_end()
            page.title = title
            return ComponentNode("title", name=title)
        if self.match("TYPE"):
            page_type = self.consume_word("Expected page type after type")
            page.page_type = page_type
            self.consume_statement_end()
            return ComponentNode("type", name=page_type)
        if self.match("HERO"):
            return self.hero_component()
        if self.match("SECTION"):
            return self.section_component()
        if self.match("ESTIMATOR"):
            name = self.consume_dotted_name("Expected estimator name")
            self.consume_statement_end()
            return ComponentNode("estimator", name=name)
        if self.match("LAYOUT"):
            name = self.consume_word("Expected layout name")
            self.consume_statement_end()
            return ComponentNode("layout", name=name)
        if self.match("SIDEBAR"):
            return self.link_container("sidebar")
        if self.match("NAVBAR"):
            return self.link_container("navbar")
        if self.match("CARD"):
            return self.card_component()
        if self.match("CHART"):
            return self.chart_component()
        if self.check_value("catalog"):
            self.advance()
            return self.catalog_component()
        if self.check_value("cart"):
            self.advance()
            return self.cart_component()
        if self.check_value("checkout"):
            self.advance()
            return self.checkout_component()
        if self.match("FORM"):
            return self.form_component()
        if self.match("TABLE"):
            return self.table_component()
        if self.match("MODAL"):
            return self.modal_component()
        if self.match("BUTTON"):
            return self.button_component()
        if self.match("USE"):
            kind = self.consume_word("Expected page use target")
            name = self.consume_word(f"Expected name after use {kind}")
            self.consume_statement_end()
            return ComponentNode(f"use_{kind}", name=name)
        return self.statement()

    def hero_component(self) -> ComponentNode:
        props: dict[str, Any] = {}
        self.consume("LBRACE", "Expected '{' after hero")
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            if self.check_value("title"):
                self.advance()
                props["title"] = self.consume_title_value("Expected hero title")
            elif self.match("SUBTITLE"):
                props["subtitle"] = self.consume_title_value("Expected hero subtitle")
            elif self.match("TEXT"):
                props["text"] = self.consume_title_value("Expected hero text")
            elif self.match("ACTION"):
                label = self.consume_title_value("Expected action label")
                target = ""
                if self.match("TO"):
                    target = self.consume_title_value("Expected action target")
                props["action"] = label
                props["to"] = target
            else:
                key = self.consume_word("Expected hero property")
                props[key] = self.consume_title_value(f"Expected value after hero {key}")
            self.consume_statement_end()
        self.consume("RBRACE", "Expected '}' to close hero")
        self.consume_statement_end()
        return ComponentNode("hero", props=props)

    def section_component(self) -> ComponentNode:
        name = self.consume_word("Expected section name")
        source = ""
        if self.match("FROM"):
            source = self.consume_word("Expected table/entity after from")
        self.consume_statement_end()
        return ComponentNode("section", name=name, props={"source": source})

    def apply_require(self, target: Any) -> None:
        if self.match("AUTH"):
            target.requires_auth = True
            return
        if self.match("ROLE"):
            target.required_role = self.consume_word("Expected role name after 'require role'")
            target.requires_auth = True
            return
        raise NovaSyntaxError("Expected 'require auth' or 'require role Name'", self.peek())

    def link_container(self, kind: str) -> ComponentNode:
        self.consume("LBRACE", f"Expected '{{' after {kind}")
        links: List[ComponentNode] = []
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            self.consume("LINK", f"Expected link inside {kind}")
            label = self.consume_title_value("Expected quoted link label")
            self.consume("TO", "Expected 'to' in link declaration")
            target = self.consume_title_value("Expected quoted link target")
            links.append(ComponentNode("link", name=label, props={"target": target}))
            self.consume_statement_end()

        self.consume("RBRACE", f"Expected '}}' to close {kind}")
        self.consume_statement_end()
        return ComponentNode(kind, children=links)

    def card_component(self) -> ComponentNode:
        title = self.consume_title_value("Expected card title")
        props: dict[str, Any] = {}
        if self.match("LBRACE"):
            while not self.check("RBRACE") and not self.at_end():
                self.skip_newlines()
                if self.check("RBRACE"):
                    break
                if self.match("VALUE"):
                    props["value"] = self.expression()
                elif self.match("TEXT"):
                    props["text"] = self.expression()
                else:
                    key = self.consume_word("Expected card property name")
                    props[key] = self.expression()
                self.consume_statement_end()
            self.consume("RBRACE", "Expected '}' to close card block")
        self.consume_statement_end()
        return ComponentNode("card", name=title, props=props)

    def chart_component(self) -> ComponentNode:
        source = self.consume_word("Expected chart source table")
        props = {"type": "line", "x": "", "y": ""}
        if self.match("LBRACE"):
            while not self.check("RBRACE") and not self.at_end():
                self.skip_newlines()
                if self.check("RBRACE"):
                    break
                key = self.consume_word("Expected chart property name")
                if key not in {"type", "x", "y"}:
                    raise NovaSyntaxError("Charts support type, x, and y properties", self.previous())
                props[key] = self.consume_word(f"Expected value after chart {key}")
                self.consume_statement_end()
            self.consume("RBRACE", "Expected '}' to close chart block")
        self.consume_statement_end()
        return ComponentNode("chart", name=source, props=props)

    def catalog_component(self) -> ComponentNode:
        table_name = self.consume_word("Expected catalog table name")
        props: dict[str, Any] = {"actions": ["add_to_cart"], "fields": []}
        if self.match("LBRACE"):
            while not self.check("RBRACE") and not self.at_end():
                self.skip_newlines()
                if self.check("RBRACE"):
                    break
                if self.match("FIELDS"):
                    props["fields"] = self.name_list_until_line_or_brace()
                elif self.match("ACTIONS"):
                    props["actions"] = self.name_list_until_line_or_brace()
                else:
                    raise NovaSyntaxError("Catalog components support fields and actions", self.peek())
                self.consume_statement_end()
            self.consume("RBRACE", "Expected '}' to close catalog block")
        self.consume_statement_end()
        return ComponentNode("catalog", name=table_name, props=props)

    def cart_component(self) -> ComponentNode:
        table_name = self.consume_word("Expected cart table name")
        props: dict[str, Any] = {"fields": []}
        if self.match("LBRACE"):
            while not self.check("RBRACE") and not self.at_end():
                self.skip_newlines()
                if self.check("RBRACE"):
                    break
                if self.match("FIELDS"):
                    props["fields"] = self.name_list_until_line_or_brace()
                else:
                    raise NovaSyntaxError("Cart components support fields", self.peek())
                self.consume_statement_end()
            self.consume("RBRACE", "Expected '}' to close cart block")
        self.consume_statement_end()
        return ComponentNode("cart", name=table_name, props=props)

    def checkout_component(self) -> ComponentNode:
        table_name = self.consume_word("Expected checkout order table name")
        props: dict[str, Any] = {"fields": [], "submit": "Place Order"}
        if self.match("LBRACE"):
            while not self.check("RBRACE") and not self.at_end():
                self.skip_newlines()
                if self.check("RBRACE"):
                    break
                if self.match("FIELDS"):
                    props["fields"] = self.name_list_until_line_or_brace()
                elif self.match("SUBMIT"):
                    props["submit"] = self.consume_title_value("Expected checkout submit text")
                else:
                    raise NovaSyntaxError("Checkout components support fields and submit", self.peek())
                self.consume_statement_end()
            self.consume("RBRACE", "Expected '}' to close checkout block")
        self.consume_statement_end()
        return ComponentNode("checkout", name=table_name, props=props)

    def form_component(self) -> ComponentNode:
        table_name = self.consume_word("Expected form table name")
        props: dict[str, Any] = {"fields": [], "submit": "Save"}
        if self.match("LBRACE"):
            while not self.check("RBRACE") and not self.at_end():
                self.skip_newlines()
                if self.check("RBRACE"):
                    break
                if self.match("FIELDS"):
                    props["fields"] = self.name_list_until_line_or_brace()
                elif self.match("SUBMIT"):
                    props["submit"] = self.consume_title_value("Expected submit button text")
                else:
                    raise NovaSyntaxError("Forms support fields and submit properties", self.peek())
                self.consume_statement_end()
            self.consume("RBRACE", "Expected '}' to close form block")
        self.consume_statement_end()
        return ComponentNode("form", name=table_name, props=props)

    def table_component(self) -> ComponentNode:
        table_name = self.consume_word("Expected table source name")
        props: dict[str, Any] = {"columns": [], "actions": []}
        if self.match("LBRACE"):
            while not self.check("RBRACE") and not self.at_end():
                self.skip_newlines()
                if self.check("RBRACE"):
                    break
                if self.match("COLUMNS"):
                    props["columns"] = self.name_list_until_line_or_brace()
                elif self.match("ACTIONS"):
                    props["actions"] = self.name_list_until_line_or_brace()
                else:
                    raise NovaSyntaxError("Table components support columns and actions", self.peek())
                self.consume_statement_end()
            self.consume("RBRACE", "Expected '}' to close table block")
        self.consume_statement_end()
        return ComponentNode("table", name=table_name, props=props)

    def modal_component(self) -> ComponentNode:
        title = self.consume_title_value("Expected modal title")
        props: dict[str, Any] = {"text": "", "button": "Close"}
        self.consume("LBRACE", "Expected '{' after modal title")
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            if self.match("TEXT"):
                value = self.expression()
                props["text"] = value.value if isinstance(value, LiteralNode) else value
            elif self.match("BUTTON"):
                props["button"] = self.consume_title_value("Expected modal button label")
            else:
                raise NovaSyntaxError("Modals support text and button properties", self.peek())
            self.consume_statement_end()
        self.consume("RBRACE", "Expected '}' to close modal block")
        self.consume_statement_end()
        return ComponentNode("modal", name=title, props=props)

    def button_component(self) -> ComponentNode:
        label = self.consume_title_value("Expected button label")
        props: dict[str, Any] = {}
        if self.match("TO"):
            props["to"] = self.consume_title_value("Expected button target after to")
        self.consume_statement_end()
        return ComponentNode("button", name=label, props=props)

    def function_declaration(self) -> FunctionNode:
        name = self.consume_word("Expected function name")
        self.consume("LPAREN", "Expected '(' after function name")
        params: List[str] = []
        if not self.check("RPAREN"):
            while True:
                params.append(self.consume_word("Expected parameter name"))
                if not self.match("COMMA"):
                    break
        self.consume("RPAREN", "Expected ')' after function parameters")
        body = self.block("function")
        self.consume_statement_end()
        return FunctionNode(name, params, body)

    def class_declaration(self) -> ClassNode:
        name = self.consume_word("Expected class name after 'class'")
        parent = ""
        if self.match("EXTENDS"):
            parent = self.consume_word("Expected parent class name after 'extends'")
        methods: List[FunctionNode] = []
        self.consume("LBRACE", "Expected '{' after class name")
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            self.consume("FUNCTION", "Classes currently contain function methods")
            methods.append(self.function_declaration())
        self.consume("RBRACE", "Expected '}' to close class block")
        self.consume_statement_end()
        return ClassNode(name, methods, parent)

    def let_statement(self) -> LetNode:
        name = self.consume_word("Expected variable name after 'let'")
        self.consume("EQUAL", "Expected '=' after variable name")
        expression = self.expression()
        self.consume_statement_end()
        return LetNode(name, expression)

    def assignment_statement(self) -> AssignNode:
        name = self.assignment_target()
        self.consume("EQUAL", "Expected '=' in assignment")
        expression = self.expression()
        self.consume_statement_end()
        return AssignNode(name, expression)

    def assignment_target(self) -> Any:
        expr: Any = IdentifierNode(self.consume_word("Expected assignment target"))
        while True:
            if self.match("DOT"):
                name = self.consume_word("Expected property name after '.'")
                if not isinstance(expr, IdentifierNode):
                    raise NovaSyntaxError("Only named values can use dotted assignment targets", self.previous())
                expr = IdentifierNode(expr.name + "." + name)
            elif self.match("LBRACKET"):
                index = self.expression()
                self.consume("RBRACKET", "Expected ']' after assignment index")
                expr = IndexNode(expr, index)
            else:
                break
        return expr.name if isinstance(expr, IdentifierNode) else expr

    def print_statement(self) -> PrintNode:
        if self.match("LPAREN"):
            expression = self.expression()
            self.consume("RPAREN", "Expected ')' after print expression")
        else:
            expression = self.expression()
        self.consume_statement_end()
        return PrintNode(expression)

    def if_statement(self) -> IfNode:
        condition = self.expression()
        then_body = self.block("if")
        self.skip_newlines()
        else_body: List[Any] = []
        if self.match("ELSE"):
            if self.match("IF"):
                else_body = [self.if_statement()]
            elif self.match("ELIF"):
                else_body = [self.if_statement()]
            else:
                else_body = self.block("else")
        elif self.match("ELIF"):
            else_body = [self.if_statement()]
        self.consume_statement_end()
        return IfNode(condition, then_body, else_body)

    def while_statement(self) -> WhileNode:
        condition = self.expression()
        body = self.block("while")
        self.consume_statement_end()
        return WhileNode(condition, body)

    def for_statement(self) -> ForNode:
        name = self.consume_word("Expected loop variable after 'for'")
        self.consume("IN", "Expected 'in' after loop variable")
        iterable = self.expression()
        body = self.block("for")
        self.consume_statement_end()
        return ForNode(name, iterable, body)

    def try_catch_statement(self) -> TryCatchNode:
        try_body = self.block("try")
        self.skip_newlines()
        self.consume("CATCH", "Expected catch block after try")
        error_name = self.consume_word("Expected error name after catch")
        catch_body = self.block("catch")
        self.consume_statement_end()
        return TryCatchNode(try_body, error_name, catch_body)

    def return_statement(self, already_matched: bool = False) -> ReturnNode:
        if not already_matched:
            pass
        if self.check("NEWLINE") or self.check("RBRACE") or self.check("EOF"):
            expression = None
        else:
            expression = self.expression()
        self.consume_statement_end()
        return ReturnNode(expression)

    def block(self, label: str) -> List[Any]:
        self.consume("LBRACE", f"Expected '{{' after {label} condition/header")
        statements: List[Any] = []
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            statements.append(self.statement())
        self.consume("RBRACE", f"Expected '}}' to close {label} block")
        return statements

    def expression(self) -> Any:
        return self.or_expression()

    def or_expression(self) -> Any:
        expr = self.and_expression()
        while self.match("OR_OR"):
            operator = self.previous().value
            right = self.and_expression()
            expr = BinaryOpNode(expr, operator, right)
        return expr

    def and_expression(self) -> Any:
        expr = self.equality()
        while self.match("AND_AND"):
            operator = self.previous().value
            right = self.equality()
            expr = BinaryOpNode(expr, operator, right)
        return expr

    def equality(self) -> Any:
        expr = self.comparison()
        while self.match("EQUAL_EQUAL", "BANG_EQUAL"):
            operator = self.previous().value
            right = self.comparison()
            expr = BinaryOpNode(expr, operator, right)
        return expr

    def comparison(self) -> Any:
        expr = self.term()
        while self.match("GREATER", "GREATER_EQUAL", "LESS", "LESS_EQUAL"):
            operator = self.previous().value
            right = self.term()
            expr = BinaryOpNode(expr, operator, right)
        return expr

    def term(self) -> Any:
        expr = self.factor()
        while self.match("PLUS", "MINUS"):
            operator = self.previous().value
            right = self.factor()
            expr = BinaryOpNode(expr, operator, right)
        return expr

    def factor(self) -> Any:
        expr = self.unary()
        while self.match("STAR", "SLASH"):
            operator = self.previous().value
            right = self.unary()
            expr = BinaryOpNode(expr, operator, right)
        return expr

    def unary(self) -> Any:
        if self.match("MINUS"):
            return UnaryOpNode("-", self.unary())
        return self.call()

    def call(self) -> Any:
        expr = self.primary()
        while True:
            if self.match("DOT"):
                name = self.consume_word("Expected property name after '.'")
                if isinstance(expr, IdentifierNode):
                    expr = IdentifierNode(expr.name + "." + name)
                else:
                    raise NovaSyntaxError("Only identifiers can use dotted calls in NovaDev 1.1", self.previous())
            elif self.match("LPAREN"):
                args: List[Any] = []
                if not self.check("RPAREN"):
                    while True:
                        args.append(self.expression())
                        if not self.match("COMMA"):
                            break
                self.consume("RPAREN", "Expected ')' after arguments")
                expr = CallNode(expr, args)
            elif self.match("LBRACKET"):
                index = self.expression()
                self.consume("RBRACKET", "Expected ']' after index expression")
                expr = IndexNode(expr, index)
            else:
                break
        return expr

    def primary(self) -> Any:
        if self.match("NUMBER", "STRING", "BOOLEAN", "NIL"):
            return LiteralNode(self.previous().value)
        if self.match("LBRACKET"):
            return self.list_literal()
        if self.match("LBRACE"):
            return self.object_literal()
        if self.check_any(NAME_TOKENS):
            return IdentifierNode(self.advance().value)
        if self.match("LPAREN"):
            self.skip_newlines()
            if self.match("RPAREN"):
                return TupleNode([])
            expr = self.expression()
            if self.match("COMMA"):
                items = [expr]
                self.skip_newlines()
                if not self.check("RPAREN"):
                    while True:
                        items.append(self.expression())
                        if not self.match("COMMA"):
                            break
                        self.skip_newlines()
                        if self.check("RPAREN"):
                            break
                self.consume("RPAREN", "Expected ')' after tuple literal")
                return TupleNode(items)
            self.consume("RPAREN", "Expected ')' after expression")
            return expr
        raise NovaSyntaxError("Expected expression", self.peek())

    def list_literal(self) -> ListNode:
        items: List[Any] = []
        self.skip_newlines()
        if not self.check("RBRACKET"):
            while True:
                items.append(self.expression())
                if not self.match("COMMA"):
                    break
                self.skip_newlines()
                if self.check("RBRACKET"):
                    break
        self.consume("RBRACKET", "Expected ']' after list literal")
        return ListNode(items)

    def object_literal(self) -> ObjectNode:
        entries: dict[str, Any] = {}
        self.skip_newlines()
        if not self.check("RBRACE"):
            while True:
                key = self.consume_word("Expected object key")
                self.consume("COLON", "Expected ':' after object key")
                entries[key] = self.expression()
                if self.match("COMMA"):
                    self.skip_newlines()
                    if self.check("RBRACE"):
                        break
                    continue
                if self.check("NEWLINE"):
                    self.skip_newlines()
                    if self.check("RBRACE"):
                        break
                    continue
                break
        self.consume("RBRACE", "Expected '}' after object literal")
        return ObjectNode(entries)

    def raw_block_source(self) -> str:
        depth = 1
        tokens: List[Token] = []
        while not self.at_end() and depth > 0:
            token = self.advance()
            if token.type == "LBRACE":
                depth += 1
                tokens.append(token)
            elif token.type == "RBRACE":
                depth -= 1
                if depth > 0:
                    tokens.append(token)
            else:
                tokens.append(token)
        if depth != 0:
            raise NovaSyntaxError("Unterminated raw code block", self.previous())
        return tokens_to_source(tokens)

    def filesystem_declaration(self) -> FilesystemNode:
        node = FilesystemNode()
        self.consume("LBRACE", "Expected '{' after filesystem")
        node.entries = self.filesystem_entries("filesystem")
        self.consume("RBRACE", "Expected '}' to close filesystem")
        self.consume_statement_end()
        return node

    def filesystem_entries(self, owner: str) -> List[Any]:
        entries: List[Any] = []
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            if self.match("FOLDER"):
                entries.append(self.folder_node())
            elif self.match("FILE"):
                entries.append(self.file_node())
            elif self.match("TEMPLATE"):
                entries.append(TemplateNode(self.consume_path_name("Expected template name")))
                self.consume_statement_end()
            elif self.match("USE"):
                self.consume("TEMPLATE", "Expected 'template' after 'use' in filesystem")
                entries.append(TemplateNode(self.consume_path_name("Expected template name")))
                self.consume_statement_end()
            elif self.match("IGNORE"):
                entries.append(self.ignore_node())
            elif self.match("RESOURCES"):
                entries.append(ResourceNode(self.container_entries("resources")))
            elif self.match("ASSETS"):
                entries.append(AssetNode(self.container_entries("assets")))
            elif self.match("PYTHON"):
                entries.append(SourceFileNode("python", self.consume_path_name("Expected Python file path")))
                self.consume_statement_end()
            elif self.match("JS") or self.match("JAVASCRIPT"):
                entries.append(SourceFileNode("js", self.consume_path_name("Expected JavaScript file path")))
                self.consume_statement_end()
            elif self.match("CSS"):
                entries.append(SourceFileNode("css", self.consume_path_name("Expected CSS file path")))
                self.consume_statement_end()
            elif self.match("HTML"):
                entries.append(SourceFileNode("html", self.consume_path_name("Expected HTML file path")))
                self.consume_statement_end()
            elif self.match("SQL"):
                entries.append(SourceFileNode("sql", self.consume_path_name("Expected SQL file path")))
                self.consume_statement_end()
            else:
                raise NovaSyntaxError(f"Unknown {owner} entry", self.peek())
        return entries

    def folder_node(self) -> FolderNode:
        name = self.consume_path_name("Expected folder name")
        if self.match("LBRACE"):
            entries = self.filesystem_entries(f"folder {name}")
            self.consume("RBRACE", f"Expected '}}' to close folder {name}")
        else:
            entries = []
        self.consume_statement_end()
        return FolderNode(name, entries)

    def file_node(self) -> FileNode:
        name = self.consume_path_name("Expected file name")
        node = FileNode(name)
        if self.match("LBRACE"):
            while not self.check("RBRACE") and not self.at_end():
                self.skip_newlines()
                if self.check("RBRACE"):
                    break
                key = self.consume_word("Expected file property")
                if key in {"text", "python"}:
                    token = self.consume("STRING", f"Expected string content after {key}")
                    node.content_kind = key
                    node.content = token.value
                elif key == "language":
                    node.language = self.consume_word("Expected language name")
                elif key == "description":
                    node.description = self.consume_title_value("Expected description string")
                elif key == "generate":
                    node.generate = self.consume_path_name("Expected generate target")
                else:
                    raise NovaSyntaxError("Files support text, python, language, description, generate", self.previous())
                self.consume_statement_end()
            self.consume("RBRACE", f"Expected '}}' to close file {name}")
        self.consume_statement_end()
        return node

    def ignore_node(self) -> IgnoreNode:
        patterns: List[str] = []
        self.consume("LBRACE", "Expected '{' after ignore")
        while not self.check("RBRACE") and not self.at_end():
            self.skip_newlines()
            if self.check("RBRACE"):
                break
            if self.match("STRING"):
                patterns.append(self.previous().value)
            else:
                patterns.append(self.consume_path_name("Expected ignore pattern"))
            self.consume_statement_end()
        self.consume("RBRACE", "Expected '}' to close ignore")
        self.consume_statement_end()
        return IgnoreNode(patterns)

    def container_entries(self, name: str) -> List[Any]:
        self.consume("LBRACE", f"Expected '{{' after {name}")
        entries = self.filesystem_entries(name)
        self.consume("RBRACE", f"Expected '}}' to close {name}")
        self.consume_statement_end()
        return entries

    def consume_title_value(self, message: str) -> str:
        if self.match("STRING"):
            return self.previous().value
        return self.consume_word(message)

    def name_list_until_line_or_brace(self) -> List[str]:
        names: List[str] = []
        while not self.check("NEWLINE") and not self.check("RBRACE") and not self.check("EOF"):
            if self.match("COMMA"):
                continue
            names.append(self.consume_word("Expected name in list"))
        return names

    def consume_statement_end(self) -> None:
        while self.match("NEWLINE", "SEMICOLON"):
            pass

    def skip_newlines(self) -> None:
        while self.match("NEWLINE"):
            pass

    def consume_word(self, message: str) -> str:
        if self.check_any(NAME_TOKENS):
            return str(self.advance().value)
        raise NovaSyntaxError(message, self.peek())

    def consume_dotted_name(self, message: str) -> str:
        name = self.consume_word(message)
        while self.match("DOT"):
            name += "." + self.consume_word("Expected name after '.'")
        return name

    def consume_import_path(self, message: str) -> tuple[str, bool]:
        name = self.consume_word(message)
        namespace = False
        while self.match("DOT"):
            if self.match("STAR"):
                name += ".*"
                namespace = True
                break
            name += "." + self.consume_word("Expected import path segment after '.'")
        return name, namespace

    def consume_path_name(self, message: str) -> str:
        if self.match("STRING"):
            return str(self.previous().value)
        name = self.consume_word(message)
        while self.match("DOT", "SLASH", "MINUS"):
            separator = "." if self.previous().type == "DOT" else "/" if self.previous().type == "SLASH" else "-"
            name += separator + self.consume_word("Expected path segment after path separator")
        return name

    def is_assignment_start(self) -> bool:
        if not self.check_any(NAME_TOKENS):
            return False
        index = self.current + 1
        while index < len(self.tokens):
            if self.tokens[index].type == "DOT" and index + 1 < len(self.tokens) and self.tokens[index + 1].type in NAME_TOKENS:
                index += 2
                continue
            if self.tokens[index].type == "LBRACKET":
                depth = 1
                index += 1
                while index < len(self.tokens) and depth > 0:
                    if self.tokens[index].type == "LBRACKET":
                        depth += 1
                    elif self.tokens[index].type == "RBRACKET":
                        depth -= 1
                    index += 1
                continue
            break
        return index < len(self.tokens) and self.tokens[index].type == "EQUAL"

    def check_value(self, value: str) -> bool:
        return str(self.peek().value).lower() == value.lower()

    def is_use_theme(self, node: Any) -> bool:
        return isinstance(node, ComponentNode) and node.kind == "use_theme"

    def match(self, *types: str) -> bool:
        if self.check_any(types):
            self.advance()
            return True
        return False

    def consume(self, token_type: str, message: str) -> Token:
        if self.check(token_type):
            return self.advance()
        raise NovaSyntaxError(message, self.peek())

    def check(self, token_type: str) -> bool:
        if self.at_end():
            return token_type == "EOF"
        return self.peek().type == token_type

    def check_any(self, types: Iterable[str]) -> bool:
        if self.at_end():
            return False
        return self.peek().type in types

    def check_next(self, token_type: str) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == token_type

    def advance(self) -> Token:
        if not self.at_end():
            self.current += 1
        return self.previous()

    def at_end(self) -> bool:
        return self.peek().type == "EOF"

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]


class NovaParser(Parser):
    """Compatibility wrapper: old code passed source text directly."""

    def __init__(self, source: str):
        super().__init__(Lexer(source).tokenize())


def parse_source(source: str) -> Program:
    return NovaParser(source).parse()


def tokens_to_source(tokens: List[Token]) -> str:
    parts: List[str] = []
    previous_type = ""
    no_space_before = {"RPAREN", "RBRACKET", "RBRACE", "COMMA", "DOT", "COLON"}
    no_space_after = {"LPAREN", "LBRACKET", "LBRACE", "DOT"}
    for token in tokens:
        if token.type == "NEWLINE":
            parts.append("\n")
            previous_type = token.type
            continue
        text = token_text(token)
        if (
            parts
            and not parts[-1].endswith(("\n", " "))
            and token.type not in no_space_before
            and previous_type not in no_space_after
        ):
            parts.append(" ")
        parts.append(text)
        previous_type = token.type
    return "".join(parts).strip()


def token_text(token: Token) -> str:
    if token.type == "STRING":
        return repr(token.value)
    if token.type == "BOOLEAN":
        return "True" if token.value else "False"
    if token.type == "NIL":
        return "None"
    return str(token.value)
