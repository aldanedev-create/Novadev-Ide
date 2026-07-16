# Python To NovaDev

NovaDev 0.4 borrows beginner-friendly Python ideas but keeps a smaller grammar.

| Python idea | NovaDev syntax |
| --- | --- |
| variable | `let name = "Aldane"` |
| f-string | `print("Hello {name}")` |
| list | `let items = [1, 2, 3]` |
| dictionary | `let user = { name: "Aldane" }` |
| `if/elif/else` | `if x > 5 { ... } elif x > 2 { ... } else { ... }` |
| `while` loop | `while x < 10 { x = x + 1 }` |
| `for` loop | `for item in items { print(item) }` |
| function | `function greet(name) { return "Hi {name}" }` |
| class | `class User { function init(name) { self.name = name } }` |
| exception | `try { ... } catch NovaNameError { ... }` |

Python uses indentation for blocks. NovaDev uses braces:

```nova
if loggedIn {
    print("Welcome")
}
```

NovaDev method names are beginner-oriented:

```nova
items.add("new")
items.length()
items.sort()
items.reverse()
```

The goal is not to replace Python. The goal is to show how a higher-level
language can sit on top of Python concepts and generate useful projects.
