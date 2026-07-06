export const examples = [
  {
    id: "hello",
    title: "Hello NovaDev",
    phase: "Phase 1",
    description: "Variables, strings, interpolation, lists, objects, indexing, and expression echo.",
    code: `let name = "Aldane"
let skills = ["NovaDev", "Python", "Vue"]
let profile = { name: name, role: "Developer" }

print("Hello {name}")
print(skills[0])
print("Role: {profile.role}")
3 + 4`,
  },
  {
    id: "control",
    title: "Control Flow",
    phase: "Phase 1",
    description: "If/else, while loops, functions, and dynamic variables.",
    code: `let count = 1

while count <= 3 {
    print("Step {count}")
    count = count + 1
}

function badge(name) {
    return "NovaDev user: " + name
}

print(badge("Aldane"))`,
  },
  {
    id: "dashboard",
    title: "Dashboard App",
    phase: "Phase 2",
    description: "Tables and pages that can become an admin UI preview.",
    code: `app BusinessAdmin {
    mode dashboard

    table Product {
        id auto
        name text required
        price number
        stock number
    }

    page Dashboard {
        type dashboard
        card "Products" value Product.count()
        table Product {
            columns name price stock
            actions edit delete
        }
    }
}`,
  },
  {
    id: "ecommerce",
    title: "Ecommerce Sketch",
    phase: "Phase 2",
    description: "A higher-level project declaration that the preview can inspect safely.",
    code: `app NovaShop {
    mode ecommerce

    table Product {
        id auto
        title text required
        price number
        image text
        rating number
    }

    table Order {
        id auto
        customer text
        total number
        status text
    }

    page Storefront {
        type landing
        hero "NovaShop"
        subtitle "A clean ecommerce storefront generated from NovaDev"
        card "Featured Products" value Product.count()
    }

    page Admin {
        type dashboard
        table Product {
            columns title price rating
            actions edit delete
        }
        table Order {
            columns customer total status
            actions view update
        }
    }
}`,
  },
  {
    id: "shell",
    title: "Browser Shell",
    phase: "Phase 3",
    description: "Use the Shell tab to run one line at a time while the browser replays session code.",
    code: `let name = "Aldane"
let active = true
let skills = ["NovaDev", "Python", "Vue"]

print("Ready, {name}")
print(skills[2])`,
  },
];

export const starterCode = examples[0].code;
