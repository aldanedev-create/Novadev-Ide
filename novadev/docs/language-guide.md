# NovaDev 0.4 Language Guide

NovaDev 0.4 is Python-inspired, but it uses braces for blocks so the parser stays
easy to understand.

## Variables

```nova
let name = "Aldane"
let age = 21
let active = true
let missing = nil
```

Strings support interpolation:

```nova
print("Hello {name}")
```

## Lists

```nova
let users = ["Aldane", "Mira"]
users.add("Jay")
users.remove("Mira")
print(users.length())
```

Loop over a list:

```nova
for user in users {
    print(user)
}
```

Loop over a range:

```nova
for number in range(1, 5) {
    print(number)
}
```

## Objects

Objects are dictionary-like values:

```nova
let user = {
    name: "Aldane",
    role: "Admin"
}

print(user.name)
user.email = "aldane@example.com"
```

## Control Flow

```nova
if score >= 90 {
    print("excellent")
} elif score >= 80 {
    print("good")
} else {
    print("try again")
}
```

Loops support `break` and `continue`:

```nova
let count = 0
while count < 10 {
    count = count + 1
    if count == 5 {
        continue
    }
    print(count)
}
```

## Functions

```nova
function add(a, b) {
    return a + b
}

print(add(2, 3))
```

## Classes

```nova
class Customer {
    function init(name) {
        self.name = name
    }

    function label() {
        return "Customer {self.name}"
    }
}

let customer = Customer("Aldane")
print(customer.label())
```

## Errors

```nova
try {
    print(missingValue)
} catch NovaNameError {
    print("Missing value handled")
}
```
