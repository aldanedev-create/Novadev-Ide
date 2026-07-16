# NovaDev Python Bridge

NovaDev exposes selected Python standard-library features through `Nova.*`.

```nova
let root = Nova.math.sqrt(81)
let roll = Nova.random.randint(1, 6)
let id = Nova.uuid.uuid4()
```

Useful bridge modules:

```txt
Nova.math
Nova.random
Nova.datetime
Nova.json
Nova.files
Nova.csv
Nova.sqlite
Nova.regex
Nova.uuid
Nova.crypto
Nova.http
Nova.email
Nova.os.safe
Nova.path
Nova.time
Nova.statistics
```

File helpers:

```nova
Nova.files.write("notes/hello.txt", "Hello")
let text = Nova.files.read("notes/hello.txt")
Nova.files.append("notes/hello.txt", "\nAgain")
```

JSON helpers:

```nova
let data = { name: "Aldane", role: "Admin" }
let encoded = Nova.json.pretty(data)
print(encoded)
```

The bridge is intentionally small. It is a safe learning surface, not full
unrestricted Python execution.
