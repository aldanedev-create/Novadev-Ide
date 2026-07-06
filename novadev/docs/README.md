# NovaDev 1.1 Documentation

NovaDev 1.1 is a Python-based programming language plus a project architecture
system. These docs explain both sides: the general-purpose language you can run
in the shell and the high-level app declarations that generate full-stack
projects.

Recommended reading order:

- [Mini Book: Building Custom Projects](mini-book-custom-projects.md)
- [Project-Specific Generation](project-specific-generation.md)
- [Tailwind Styling](tailwind-styling.md)
- [Package Manager](package-manager.md)
- [Windows Installer And GUI](windows-installer-and-gui.md)
- [ProjectIR](project-ir.md)
- [Modes](modes.md)
- [Mode Custom](mode-custom.md)
- [Workflows](workflows.md)
- [Page Types](page-types.md)
- [Modules](modules.md)
- [Python Modules](python-modules.md)
- [Examples 1.1](examples-1.1.md)
- [Language Guide](language-guide.md)
- [General-Purpose Core](general-purpose-core.md)
- [Project Layer](project-layer.md)
- [Python Bridge](python-bridge.md)
- [JavaScript Escape Hatch](javascript-escape-hatch.md)
- [Module System](module-system.md)
- [Plugin System](plugin-system.md)
- [File Structure System](file-structure-system.md)
- [Stack Targets](stack-targets.md)
- [Generated Projects](generated-projects.md)
- [Custom Code](custom-code.md)
- [CLI](cli.md)
- [Examples](examples.md)

Implementation prompts:

- [NovaDev 1.1 Project-Specific Code Generation Prompt](prompts/novadev-1.1-project-specific-codegen-prompt.md)
- [NovaDev 1.1 Project-Specific Generator Implementation Prompt](prompts/novadev-1.1-project-specific-generators-implementation-prompt.md)
- [NovaDev Tailwind + ProjectIR Styling Prompt](prompts/novadev-tailwind-projectir-styling-prompt.md)

Useful commands:

```bash
python shell.py
python nova.py run examples/scripts/math_tool.nova
python nova.py run examples/scripts/project_planner.nova
python novapm.py install packages/hello-ui
python nova.py build-fullstack examples/apps/webshield
```
