export const lessons = [
  {
    id: "welcome",
    section: "Getting Started",
    level: "Beginner",
    title: "Welcome to NovaDev",
    summary: "Understand NovaDev as both a programming language and an app-building language.",
    concepts: ["source code", "tokens", "AST", "runtime", "project generation"],
    outcomes: [
      "Know what NovaDev source code is.",
      "Understand the path from code to tokens, AST nodes, runtime execution, and generated project files.",
      "See how NovaDev can act like a normal language and a higher-level app compiler.",
    ],
    explanation:
      "NovaDev starts like other programming languages: you write source code, the lexer turns it into tokens, the parser builds an AST, and the interpreter/runtime executes it. NovaDev also has app declarations that describe pages, tables, routes, workflows, frontend files, backend files, and project architecture.",
    code: `print("Welcome to NovaDev")

app FirstProject {
    project {
        frontend Vue
        backend Flask
        database SQLite
        structure VueFlask
        styling Tailwind
        mode custom
    }

    page Home {
        title "My First NovaDev App"
    }
}`,
    exercise: "Change the app name and page title, then run Tokens and AST to see how the language reads it.",
    projectUse:
      "Use this mental model for every NovaDev project: normal code handles logic, while app declarations describe the project you want generated.",
  },
  {
    id: "print-output",
    section: "Getting Started",
    level: "Beginner",
    title: "Printing Output",
    summary: "Use print to show text and values in the terminal or online IDE output page.",
    concepts: ["print", "strings", "output", "debugging"],
    outcomes: [
      "Print plain text.",
      "Use print as a beginner-friendly debugging tool.",
      "Understand why output matters when testing language features.",
    ],
    explanation:
      "The simplest way to see a program do something is to print output. In NovaDev, print works like Python's first lesson: start small, run it, observe the result, then change it.",
    code: `print("Hello NovaDev")
print("I can run code in the shell")
print("I can also generate apps")`,
    exercise: "Add three print lines that describe a project you want to build.",
    projectUse:
      "Use print while building workflows, calculations, checkout logic, reports, and small utilities before generating the full app.",
  },
  {
    id: "variables",
    section: "Getting Started",
    level: "Beginner",
    title: "Variables with Let",
    summary: "Store values in names so your program can reuse them.",
    concepts: ["let", "variables", "assignment", "dynamic typing"],
    outcomes: [
      "Create variables with let.",
      "Update variables after they are created.",
      "Understand NovaDev's dynamic high-level style.",
    ],
    explanation:
      "Variables let you name information. NovaDev is dynamic, so the same language can store strings, numbers, booleans, lists, and objects without a long type ceremony.",
    code: `let name = "Aldane"
let age = 20

print(name)
print(age)

age = age + 1
print(age)`,
    exercise: "Create variables for a product name, price, and stock count. Print all three.",
    projectUse:
      "Variables are used for totals, API responses, settings, user input, workflow state, and generated backend calculations.",
  },
  {
    id: "strings",
    section: "Getting Started",
    level: "Beginner",
    title: "Strings and Interpolation",
    summary: "Build readable messages with string values and interpolation.",
    concepts: ["strings", "interpolation", "text", "templates"],
    outcomes: [
      "Store text in variables.",
      "Insert variable values into strings with braces.",
      "Create human-readable messages for pages and backend output.",
    ],
    explanation:
      "NovaDev supports string interpolation with braces. This makes messages easier to write because you do not have to manually join every piece of text.",
    code: `let customer = "Maya"
let product = "Honeycrisp Box"
let total = 29

print("Customer {customer} ordered {product}")
print("Total: {total}")`,
    exercise: "Make a welcome message that includes a user's name and role.",
    projectUse:
      "Interpolation is useful for receipts, notifications, dashboard labels, route messages, and generated UI text.",
  },
  {
    id: "numbers-booleans-nil",
    section: "Getting Started",
    level: "Beginner",
    title: "Numbers, Booleans, and Nil",
    summary: "Use numbers for math, booleans for decisions, and nil/null for empty values.",
    concepts: ["numbers", "booleans", "nil", "null", "operators"],
    outcomes: [
      "Do simple arithmetic.",
      "Use true and false values.",
      "Represent missing data with nil or null.",
    ],
    explanation:
      "Most real programs need math and decisions. NovaDev supports numbers, booleans, comparisons, and empty values so you can model real app data.",
    code: `let price = 25
let quantity = 3
let active = true
let coupon = nil

print(price * quantity)
print(active)
print(coupon)`,
    exercise: "Add a discount variable and print the discounted total.",
    projectUse:
      "Use these values for prices, inventory, form status, login checks, nullable database fields, and analytics.",
  },
  {
    id: "lists",
    section: "Getting Started",
    level: "Beginner",
    title: "Lists and Indexing",
    summary: "Store many values in one variable and read items by index.",
    concepts: ["lists", "arrays", "indexing", "collections"],
    outcomes: [
      "Create a list of values.",
      "Read list items with square brackets.",
      "Use lists to model repeated data.",
    ],
    explanation:
      "Lists are ordered. The first item is at index 0, just like Python and JavaScript. NovaDev uses lists for menus, products, skills, roles, rows, and generated UI sections.",
    code: `let skills = ["NovaDev", "Python", "Vue"]

print(skills[0])
print(skills[1])
print(skills[2])`,
    exercise: "Create a list of three products and print the second product.",
    projectUse:
      "Lists help represent product grids, navbar links, table rows, uploaded files, and search results.",
  },
  {
    id: "objects",
    section: "Getting Started",
    level: "Beginner",
    title: "Objects and Dot Access",
    summary: "Group related values into one object and read fields with dot syntax.",
    concepts: ["objects", "maps", "properties", "dot access"],
    outcomes: [
      "Create object literals.",
      "Read values with dot access.",
      "Model real-world entities before making tables.",
    ],
    explanation:
      "Objects are useful when values belong together. A profile, product, order, customer, or settings record can be represented as one object.",
    code: `let profile = { name: "Aldane", role: "Developer", active: true }

print(profile.name)
print(profile.role)
print("Active: {profile.active}")`,
    exercise: "Create a product object with name, price, and stock. Print each field.",
    projectUse:
      "Objects are a bridge between normal code and full app models. Later, tables turn this kind of structure into database-backed data.",
  },
  {
    id: "operators",
    section: "Getting Started",
    level: "Beginner",
    title: "Operators",
    summary: "Use arithmetic, comparison, and logical operators.",
    concepts: ["+", "-", "*", "/", "==", "!=", "&&", "||"],
    outcomes: [
      "Calculate values with math operators.",
      "Compare values with comparison operators.",
      "Combine conditions with logical operators.",
    ],
    explanation:
      "Operators are how programs ask questions and calculate answers. NovaDev supports common operators used in Python, JavaScript, and C-style languages.",
    code: `let stock = 10
let price = 5
let total = stock * price

print(total)
print(stock > 0)
print(stock > 0 && price < 10)`,
    exercise: "Write a condition that checks if a user is active and has admin role.",
    projectUse:
      "Operators appear in checkout totals, permission checks, filters, reports, dashboards, and validation workflows.",
  },
  {
    id: "if-else",
    section: "Core Programming",
    level: "Beginner",
    title: "If and Else",
    summary: "Choose which code runs based on a condition.",
    concepts: ["if", "else", "conditions", "branches"],
    outcomes: [
      "Write an if block.",
      "Write an else block.",
      "Use comparisons to control program behavior.",
    ],
    explanation:
      "If and else give programs decision-making. A store can show sold out, an admin page can require a role, and a form can reject invalid input.",
    code: `let stock = 4

if stock > 0 {
    print("Available")
} else {
    print("Sold out")
}`,
    exercise: "Add a price check: if price is greater than 100, print Premium, otherwise print Standard.",
    projectUse:
      "Use if/else for checkout validation, role access, workflow decisions, route responses, and UI state.",
  },
  {
    id: "while-loops",
    section: "Core Programming",
    level: "Beginner",
    title: "While Loops",
    summary: "Repeat work while a condition remains true.",
    concepts: ["while", "loops", "counters", "iteration"],
    outcomes: [
      "Create a loop with while.",
      "Update a counter so the loop stops.",
      "Avoid infinite loops.",
    ],
    explanation:
      "Loops are used when code needs to repeat. NovaDev limits runaway loops in the online IDE so beginner mistakes do not lock the page forever.",
    code: `let count = 1

while count <= 5 {
    print("Packing order {count}")
    count = count + 1
}`,
    exercise: "Write a loop that counts down from 3 to 1, then prints Launch.",
    projectUse:
      "Use loops for batch processing, reports, importing records, generating repeated UI sections, and testing calculations.",
  },
  {
    id: "functions",
    section: "Core Programming",
    level: "Intermediate",
    title: "Functions",
    summary: "Wrap reusable logic into named blocks.",
    concepts: ["function", "parameters", "return", "calls"],
    outcomes: [
      "Define a function.",
      "Pass values into parameters.",
      "Return a result and reuse it.",
    ],
    explanation:
      "Functions keep programs organized. A function should usually do one job: calculate a total, validate input, format text, or prepare data for a page.",
    code: `function total(price, quantity) {
    return price * quantity
}

let subtotal = total(25, 4)
print("Subtotal: {subtotal}")`,
    exercise: "Create a function named addTax that returns amount * 1.15.",
    projectUse:
      "Use functions for pricing, validation, formatting, permission checks, and reusable workflow rules.",
  },
  {
    id: "debugging",
    section: "Core Programming",
    level: "Beginner",
    title: "Errors and Debugging",
    summary: "Learn how NovaDev reports missing variables and syntax mistakes.",
    concepts: ["runtime errors", "syntax errors", "debugging", "clear messages"],
    outcomes: [
      "Recognize missing variable errors.",
      "Use print to isolate program state.",
      "Use Tokens and AST pages to debug language structure.",
    ],
    explanation:
      "A real language needs good errors. When something fails, check the output message, inspect tokens, inspect the AST, and reduce the code to the smallest failing example.",
    code: `let name = "NovaDev"
print(name)

// Uncomment this to see a missing variable error:
// print(username)`,
    exercise: "Make a small mistake, run it, read the error, then fix it.",
    projectUse:
      "Debugging skills matter when custom project code becomes large across frontend, backend, tables, workflows, and routes.",
  },
  {
    id: "modules-use",
    section: "Core Programming",
    level: "Intermediate",
    title: "Splitting Code with Use",
    summary: "Keep large projects readable by spreading code across multiple .nova files.",
    concepts: ["use", "modules", "multi-file projects", "organization"],
    outcomes: [
      "Understand why large apps should not live in one file.",
      "Use use declarations to describe imported NovaDev files.",
      "Organize models, pages, workflows, styles, and routes.",
    ],
    explanation:
      "As projects grow, one file becomes difficult to manage. NovaDev projects can be organized into folders such as models, pages, routes, workflows, and styles, then connected from app.nova.",
    code: `use "./models/product.nova"
use "./pages/home.nova"
use "./routes/products.nova"

app AppleStore {
    project {
        frontend Vue
        backend Flask
        database SQLite
        structure VueFlask
        styling Tailwind
        mode ecommerce
    }
}`,
    exercise: "Plan a folder structure for a project with models, pages, routes, workflows, and styles.",
    projectUse:
      "Use multi-file projects for real apps such as stores, booking systems, CMS dashboards, school tools, and business portals.",
  },
  {
    id: "app-project",
    section: "Build Apps",
    level: "Beginner",
    title: "App and Project Blocks",
    summary: "Describe the full-stack architecture NovaDev should generate.",
    concepts: ["app", "project", "Vue", "Flask", "SQLite", "Tailwind"],
    outcomes: [
      "Declare an app name.",
      "Choose frontend, backend, database, structure, styling, and mode.",
      "Understand the difference between code execution and project generation.",
    ],
    explanation:
      "The app block is where NovaDev becomes more than a scripting language. It tells NovaDev what kind of software project to produce.",
    code: `app ClientPortal {
    project {
        frontend Vue
        backend Flask
        database SQLite
        structure VueFlask
        styling Tailwind
        mode custom

        architecture {
            folder docs
            folder tests
            folder uploads
        }
    }
}`,
    exercise: "Change the app to a project you want to build and add two architecture folders.",
    projectUse:
      "Use this block as the root contract between your NovaDev source and the generated application folder.",
  },
  {
    id: "modes",
    section: "Build Apps",
    level: "Beginner",
    title: "Modes: Custom and Domain Defaults",
    summary: "Choose whether NovaDev should use a domain generator or only your declarations.",
    concepts: ["mode custom", "mode ecommerce", "mode construction", "domain generators"],
    outcomes: [
      "Use mode custom when the app does not fit a preset category.",
      "Use domain modes when helpful defaults are wanted.",
      "Avoid unrelated generated code by choosing the right mode.",
    ],
    explanation:
      "Mode controls assumptions. mode ecommerce can add store defaults. mode construction can add construction defaults. mode custom should only generate what the developer explicitly declares.",
    code: `app ChurchMediaSystem {
    project {
        frontend Vue
        backend Flask
        database SQLite
        styling Tailwind
        mode custom
    }

    page Home {
        title "Church Media"
    }
}`,
    exercise: "Write one app using mode custom and one using mode ecommerce. Compare what should be generated.",
    projectUse:
      "Use modes to make NovaDev project-specific instead of producing the same generic code for every app.",
  },
  {
    id: "tables-fields",
    section: "Build Apps",
    level: "Beginner",
    title: "Tables and Fields",
    summary: "Declare data models that can become database tables and UI resources.",
    concepts: ["table", "fields", "auto", "text", "number", "date"],
    outcomes: [
      "Declare a table.",
      "Add fields with simple types.",
      "Connect tables to pages and generated backend models.",
    ],
    explanation:
      "Tables describe the app's data. In generated Flask projects, these declarations can become SQLite and SQLAlchemy models.",
    code: `table Product {
    id auto
    name text
    price number
    image text
    stock number
}

table Order {
    id auto
    customerName text
    total number
    status text
}`,
    exercise: "Create a Customer table with id, name, email, and joinedDate.",
    projectUse:
      "Tables are the foundation for admin dashboards, forms, CRUD routes, reports, and generated database models.",
  },
  {
    id: "pages-components",
    section: "Build Apps",
    level: "Beginner",
    title: "Pages and Components",
    summary: "Describe user-facing screens with page, hero, card, section, form, and chart declarations.",
    concepts: ["page", "hero", "card", "section", "form", "chart"],
    outcomes: [
      "Create pages with titles.",
      "Add hero and card content.",
      "Connect page sections to tables.",
    ],
    explanation:
      "Pages tell NovaDev what the frontend needs. They are not just decoration; they guide generated routes, navigation, dashboard panels, and UI previews.",
    code: `page Home {
    title "Apple Market"
    hero {
        title "Fresh apples delivered fast"
        subtitle "Shop orchard boxes, bundles, and seasonal picks."
        action "Shop Now"
    }
    section Products from Product
    card Featured {
        title "Honeycrisp Box"
        value "$29"
    }
}`,
    exercise: "Add a Dashboard page with two cards: Sales and Orders.",
    projectUse:
      "Use page declarations to build stores, admin tools, dashboards, learning sites, portfolios, and booking systems.",
  },
  {
    id: "routes",
    section: "Backend",
    level: "Intermediate",
    title: "Routes",
    summary: "Declare API endpoints that generated backend files can implement.",
    concepts: ["route", "GET", "POST", "return", "API"],
    outcomes: [
      "Create GET and POST routes.",
      "Understand routes as backend entry points.",
      "Plan route names around real project workflows.",
    ],
    explanation:
      "Routes are how frontend code talks to backend code. In a Flask project, NovaDev route declarations can generate starter route files.",
    code: `route GET "/api/products" {
    return "products"
}

route POST "/api/orders" {
    return "order created"
}

print("Routes declared")`,
    exercise: "Add routes for /api/customers and /api/dashboard.",
    projectUse:
      "Use routes for product lists, checkout, login, uploads, dashboards, reports, and third-party API webhooks.",
  },
  {
    id: "workflows",
    section: "Backend",
    level: "Intermediate",
    title: "Workflows",
    summary: "Describe business actions such as checkout, booking, approval, and notifications.",
    concepts: ["workflow", "input", "creates", "notify", "business logic"],
    outcomes: [
      "Understand workflows as high-level business actions.",
      "Connect workflows to tables.",
      "Plan what the generated backend should do.",
    ],
    explanation:
      "A workflow is a process, not just a page. Checkout creates an order. A booking request creates an appointment. A support ticket notifies staff.",
    code: `workflow Checkout {
    input Product
    creates Order
    notify Admin
}

workflow RestockAlert {
    input Product
    notify Manager
}`,
    exercise: "Create a workflow for ContactLead that creates Lead and notifies Sales.",
    projectUse:
      "Use workflows to describe app-specific behavior so NovaDev does not generate unrelated generic code.",
  },
  {
    id: "auth-roles",
    section: "Backend",
    level: "Intermediate",
    title: "Auth and Roles",
    summary: "Plan authentication and role-based access for generated apps.",
    concepts: ["auth", "role", "require", "permissions"],
    outcomes: [
      "Describe user roles.",
      "Connect roles to protected pages or routes.",
      "Understand auth as both frontend and backend behavior.",
    ],
    explanation:
      "Real apps often need different users: customers, admins, staff, drivers, teachers, students, or managers. NovaDev auth declarations should guide generated route guards and UI navigation.",
    code: `auth {
    role Admin
    role Customer
    role Staff
}

page AdminDashboard {
    title "Admin Dashboard"
    require role Admin
}`,
    exercise: "Add roles for Driver and Manager, then protect a Reports page.",
    projectUse:
      "Use roles in stores, CRMs, schools, booking apps, delivery systems, and internal dashboards.",
  },
  {
    id: "sqlite-sqlalchemy",
    section: "Backend",
    level: "Intermediate",
    title: "SQLite and SQLAlchemy",
    summary: "Understand how NovaDev table declarations map to real Flask database code.",
    concepts: ["SQLite", "SQLAlchemy", "models", "database"],
    outcomes: [
      "Connect table declarations to generated backend models.",
      "Understand SQLite as the starter database.",
      "Understand SQLAlchemy as the Python model layer.",
    ],
    explanation:
      "NovaDev can use SQLite for local app data and SQLAlchemy for Python model classes. The .nova file describes the table; generated backend code turns it into working database code.",
    code: `app InventoryApp {
    project {
        frontend Vue
        backend Flask
        database SQLite
        structure VueFlask
        styling Tailwind
        mode inventory
    }

    table Item {
        id auto
        name text
        sku text
        quantity number
    }
}`,
    exercise: "Add Supplier and PurchaseOrder tables for an inventory project.",
    projectUse:
      "Use SQLite and SQLAlchemy generation for dashboards, admin panels, inventory tools, store backends, school systems, and CRUD-heavy apps.",
  },
  {
    id: "vue-tailwind",
    section: "Frontend",
    level: "Intermediate",
    title: "Vue and Tailwind Generation",
    summary: "Use NovaDev declarations to generate Vue screens styled with Tailwind.",
    concepts: ["Vue", "Tailwind", "components", "responsive design"],
    outcomes: [
      "Select Vue as the frontend.",
      "Select Tailwind as the styling system.",
      "Understand why project-specific styling must come from declarations.",
    ],
    explanation:
      "Tailwind helps generated projects look different without one shared CSS file making every project feel the same. The domain, mode, theme, pages, and declared components should shape the final UI.",
    code: `app SalonBooking {
    project {
        frontend Vue
        backend Flask
        database SQLite
        structure VueFlask
        styling Tailwind
        mode booking
    }

    theme CleanStudio {
        primary "#111827"
        accent "#ec4899"
        surface "#ffffff"
    }
}`,
    exercise: "Change the app to a hotel booking site and choose different theme colors.",
    projectUse:
      "Use Vue and Tailwind when you want modern frontend projects that can still be customized after generation.",
  },
  {
    id: "custom-frontend",
    section: "Frontend",
    level: "Advanced",
    title: "Custom Frontend Code",
    summary: "Add custom frontend files when generated UI needs project-specific behavior.",
    concepts: ["custom frontend", "CSS", "JavaScript", "triple strings"],
    outcomes: [
      "Use triple-quoted strings for longer code blocks.",
      "Add custom CSS or JavaScript.",
      "Keep generated code project-specific.",
    ],
    explanation:
      "Generated defaults are helpful, but real projects need custom code. NovaDev can wrap custom frontend code so developers control exact behavior and style.",
    code: `app PortfolioCMS {
    project {
        frontend Vue
        backend Flask
        database SQLite
        styling Tailwind
        mode cms
    }

    custom frontend "styles/brand.css" """
.project-card {
    border-radius: 8px;
    border: 1px solid #e5e7eb;
}
"""

    page Home {
        title "Portfolio CMS"
    }
}`,
    exercise: "Add a custom frontend app.js block that logs when the page loads.",
    projectUse:
      "Use custom frontend blocks for branded layouts, animation hooks, charts, filters, maps, and advanced page interactions.",
  },
  {
    id: "custom-backend",
    section: "Backend",
    level: "Advanced",
    title: "Custom Backend Python",
    summary: "Wrap Python backend modules inside NovaDev for real app logic.",
    concepts: ["custom backend", "Python modules", "Flask services", "business logic"],
    outcomes: [
      "Add backend service files from .nova source.",
      "Keep business logic specific to the project.",
      "Use Python's ecosystem without hiding the generated code.",
    ],
    explanation:
      "NovaDev should not guess every business rule. For real apps, developers can declare tables and pages, then add custom backend Python modules for the project-specific parts.",
    code: `app SupportDesk {
    project {
        frontend Vue
        backend Flask
        database SQLite
        styling Tailwind
        mode supportdesk
    }

    custom backend "services/ticket_priority.py" """
def priority_for(message):
    text = message.lower()
    if "urgent" in text or "down" in text:
        return "high"
    return "normal"
"""

    table Ticket {
        id auto
        subject text
        message text
        priority text
    }
}`,
    exercise: "Create a custom backend module for calculating invoice totals.",
    projectUse:
      "Use backend modules for payments, AI calls, scoring, document processing, notifications, reports, and custom integrations.",
  },
  {
    id: "api-keys",
    section: "Advanced Tutorials",
    level: "Advanced",
    title: "API Keys and Environment Variables",
    summary: "Use API keys safely by reading them from environment variables in backend code.",
    concepts: ["API keys", "environment variables", "secrets", "backend integrations"],
    outcomes: [
      "Understand why API keys should not be hardcoded into frontend files.",
      "Read secrets from environment variables in backend Python.",
      "Plan API integrations safely in generated Flask apps.",
    ],
    explanation:
      "API keys are secrets. Put them in environment variables such as OPENAI_API_KEY, STRIPE_SECRET_KEY, or RESEND_API_KEY. The frontend should call your backend route; the backend reads the key and talks to the third-party service.",
    code: `app AiAssistant {
    project {
        frontend Vue
        backend Flask
        database SQLite
        styling Tailwind
        mode custom
    }

    custom backend "services/ai_client.py" """
import os

def get_api_key():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is missing")
    return key
"""

    route POST "/api/ai/message" {
        return "AI message route"
    }
}`,
    exercise: "Write a backend service file that reads STRIPE_SECRET_KEY without printing it.",
    projectUse:
      "Use this pattern for AI, payments, email, SMS, maps, shipping, analytics, and any service that gives you a private key.",
  },
  {
    id: "external-apis",
    section: "Advanced Tutorials",
    level: "Advanced",
    title: "Calling External APIs",
    summary: "Design routes that let your backend call third-party APIs safely.",
    concepts: ["HTTP APIs", "backend routes", "fetch", "service modules"],
    outcomes: [
      "Create a NovaDev route for an integration.",
      "Keep external API calls on the backend.",
      "Separate frontend requests from private service logic.",
    ],
    explanation:
      "The safe pattern is frontend to your backend, then backend to the external API. This protects secrets and gives your app one place to validate input and handle errors.",
    code: `app WeatherPlanner {
    project {
        frontend Vue
        backend Flask
        database SQLite
        styling Tailwind
        mode custom
    }

    custom backend "services/weather.py" """
import os
import urllib.request

def weather_url(city):
    key = os.environ.get("WEATHER_API_KEY")
    return f"https://api.example.com/weather?city={city}&key={key}"
"""

    route GET "/api/weather" {
        return "weather"
    }
}`,
    exercise: "Create a service module for an email provider and a route named /api/send-email.",
    projectUse:
      "Use external APIs for shipping rates, payment checkout, AI chat, email notifications, maps, calendars, and CRM sync.",
  },
  {
    id: "package-manager",
    section: "Advanced Tutorials",
    level: "Intermediate",
    title: "Using Packages",
    summary: "Understand how NovaDev packages can add reusable UI and backend features.",
    concepts: ["novapm", "packages", "registry", "reusable modules"],
    outcomes: [
      "Understand why a package manager matters.",
      "Use packages for reusable kits.",
      "Avoid copying the same code into every project.",
    ],
    explanation:
      "A package manager lets developers download shared capabilities like auth-kit, dashboard-kit, or hello-ui. Real language ecosystems grow because developers can reuse trusted modules.",
    code: `use package "auth-kit"
use package "dashboard-kit"

app AdminPanel {
    project {
        frontend Vue
        backend Flask
        database SQLite
        styling Tailwind
        mode dashboard
    }

    page Dashboard {
        title "Admin Dashboard"
    }
}`,
    exercise: "List three packages you would want for your own app idea.",
    projectUse:
      "Use packages for authentication, dashboards, charts, payments, notifications, form components, and starter templates.",
  },
  {
    id: "project-specific-generation",
    section: "Advanced Tutorials",
    level: "Advanced",
    title: "Project-Specific Generation",
    summary: "Make generated code match the app the developer actually described.",
    concepts: ["compiler context", "mode", "pages", "workflows", "custom modules"],
    outcomes: [
      "Understand why templates alone are not enough.",
      "Use declarations to drive specific generated code.",
      "Combine mode, tables, pages, routes, workflows, and custom modules.",
    ],
    explanation:
      "NovaDev should generate code from the project context. A church app should not get cart code unless the developer declared it. A construction site should not get school attendance logic. mode custom is the strictest version: only declared behavior.",
    code: `app ChurchMediaSystem {
    project {
        frontend Vue
        backend Flask
        database SQLite
        styling Tailwind
        mode custom
    }

    table Sermon {
        id auto
        title text
        speaker text
        videoUrl text
        date date
    }

    table PrayerRequest {
        id auto
        name text
        message text
        status text
    }

    workflow SubmitPrayer {
        input PrayerRequest
        creates PrayerRequest
        notify Admin
    }

    page Home {
        title "Church Media"
        section Sermons from Sermon
        form PrayerRequest
    }
}`,
    exercise: "Create a custom app for a gym, restaurant queue, or trading journal using only declared behavior.",
    projectUse:
      "Use this approach to make NovaDev useful for many categories without hardcoding one generic project into every output.",
  },
  {
    id: "testing",
    section: "Professional Development",
    level: "Intermediate",
    title: "Testing NovaDev Projects",
    summary: "Plan tests for language code and generated applications.",
    concepts: ["testing", "black-box testing", "unit tests", "manual checks"],
    outcomes: [
      "Test small NovaDev examples.",
      "Test generated backend routes.",
      "Test generated frontend pages.",
    ],
    explanation:
      "A production-like workflow checks language behavior and generated app behavior. Start with small examples, then test pages, routes, database models, and workflows.",
    code: `let expected = 30
let actual = 10 + 20

if actual == expected {
    print("test passed")
} else {
    print("test failed")
}`,
    exercise: "Write a small test for a total(price, quantity) function.",
    projectUse:
      "Use testing before presenting generated projects, deploying websites, or adding package-manager features.",
  },
  {
    id: "deployment",
    section: "Professional Development",
    level: "Intermediate",
    title: "Deployment Thinking",
    summary: "Understand what changes when a NovaDev app moves from local development to the internet.",
    concepts: ["deployment", "environment variables", "Vercel", "Flask hosting", "build output"],
    outcomes: [
      "Separate local development from deployment.",
      "Know where frontend, backend, database, and secrets fit.",
      "Plan what must be rebuilt before uploading.",
    ],
    explanation:
      "Deployment is not just uploading files. The frontend build, backend server, environment variables, database location, package downloads, and installer zip must all match the version you want users to receive.",
    code: `app DeployReadyApp {
    project {
        frontend Vue
        backend Flask
        database SQLite
        structure VueFlask
        styling Tailwind
        mode custom

        architecture {
            folder docs
            folder tests
            folder uploads
        }
    }

    page Home {
        title "Ready to Deploy"
    }
}`,
    exercise: "Write a deployment checklist for a NovaDev app with one API key and one database.",
    projectUse:
      "Use deployment thinking for Vercel sites, Flask backends, package-manager downloads, Windows installers, and client demos.",
  },
  {
    id: "capstone-store",
    section: "Capstone Projects",
    level: "Advanced",
    title: "Capstone: E-commerce Store",
    summary: "Combine app mode, tables, pages, workflows, routes, Vue, Flask, SQLite, and custom code.",
    concepts: ["ecommerce", "tables", "checkout", "routes", "custom backend"],
    outcomes: [
      "Build a larger NovaDev app from multiple concepts.",
      "Use ecommerce mode for helpful defaults.",
      "Add project-specific code so the output is not generic.",
    ],
    explanation:
      "A real store needs products, customers, orders, checkout workflows, pages, routes, and sometimes custom payment code. NovaDev should use the declarations to generate the right app shape.",
    code: `app AppleMarket {
    project {
        frontend Vue
        backend Flask
        database SQLite
        structure VueFlask
        styling Tailwind
        mode ecommerce
    }

    table Product {
        id auto
        name text
        price number
        image text
        stock number
    }

    table Order {
        id auto
        customerName text
        total number
        status text
    }

    workflow Checkout {
        input Product
        creates Order
        notify Admin
    }

    page Home {
        title "Apple Market"
        section Products from Product
        card Featured {
            title "Honeycrisp Box"
            value "$29"
        }
    }

    route POST "/api/checkout" {
        return "checkout"
    }
}`,
    exercise: "Add Cart, Customer, and PaymentAttempt tables, then add a custom backend payment module.",
    projectUse:
      "Use this capstone as the pattern for store projects that should look and behave like real e-commerce applications.",
  },
  {
    id: "capstone-custom-system",
    section: "Capstone Projects",
    level: "Advanced",
    title: "Capstone: Custom Business System",
    summary: "Use mode custom to build a project that does not fit a common category.",
    concepts: ["mode custom", "explicit declarations", "custom modules", "business workflows"],
    outcomes: [
      "Build a non-generic app from explicit declarations.",
      "Avoid unrelated generated features.",
      "Use custom backend and frontend blocks where the language needs developer control.",
    ],
    explanation:
      "Custom systems are where NovaDev must act most like a real compiler. The developer writes the source of truth, and NovaDev generates only what was declared.",
    code: `app TradingJournal {
    project {
        frontend Vue
        backend Flask
        database SQLite
        styling Tailwind
        mode custom
    }

    table Trade {
        id auto
        symbol text
        entry number
        exit number
        result number
        notes text
    }

    workflow LogTrade {
        input Trade
        creates Trade
        notify Trader
    }

    custom backend "services/risk.py" """
def risk_reward(entry, stop, target):
    risk = abs(entry - stop)
    reward = abs(target - entry)
    return reward / risk
"""

    page Dashboard {
        title "Trading Journal"
        section Trades from Trade
        chart Performance
    }
}`,
    exercise: "Create a custom project for a gym billing system, security scanner, or nonprofit donation tracker.",
    projectUse:
      "Use this pattern when NovaDev has no built-in domain mode for your idea, but you still want full-stack generation.",
  },
  {
    id: "classes-oop",
    section: "Object-Oriented Programming",
    level: "Intermediate",
    title: "Classes and Objects",
    summary: "Use classes to group data and behavior into reusable blueprints.",
    concepts: ["class", "object", "constructor", "method", "this"],
    outcomes: [
      "Understand why classes exist.",
      "Design objects that represent real project concepts.",
      "Know when classes are better than loose variables.",
    ],
    explanation:
      "Object-oriented programming helps organize larger applications. A class is a blueprint. An object is a live value created from that blueprint. NovaDev can teach and describe OOP concepts even when generated backend code maps them into Python classes, SQLAlchemy models, or service objects.",
    code: `class Product {
    constructor(name, price) {
        this.name = name
        this.price = price
    }

    function label() {
        return "{this.name} costs {this.price}"
    }
}

let productName = "Honeycrisp Box"
let productPrice = 29
print("{productName} costs {productPrice}")`,
    exercise: "Design a Customer class with name, email, and a display method.",
    projectUse:
      "Use classes for domain objects such as Product, Customer, Order, Booking, Ticket, Invoice, Student, Course, and Trade.",
  },
  {
    id: "oop-design",
    section: "Object-Oriented Programming",
    level: "Advanced",
    title: "OOP Design: Composition and Inheritance",
    summary: "Model relationships between objects without making code hard to change.",
    concepts: ["composition", "inheritance", "extends", "domain modeling"],
    outcomes: [
      "Understand inheritance as an is-a relationship.",
      "Understand composition as a has-a relationship.",
      "Choose the simpler design for generated projects.",
    ],
    explanation:
      "Inheritance can be useful, but composition is often easier to maintain. A Store has Products and Orders. A PremiumCustomer may extend Customer. NovaDev project generation should prefer clear data models and service modules unless inheritance truly makes the code clearer.",
    code: `class User {
    constructor(name) {
        this.name = name
    }
}

class Admin extends User {
    function canManageUsers() {
        return true
    }
}

let role = "Admin"
print("{role} can manage users")`,
    exercise: "Model a Booking that has a Customer and a Service without using inheritance.",
    projectUse:
      "Use OOP design when generated Flask services, SQLAlchemy models, or custom backend modules need clear responsibilities.",
  },
  {
    id: "automations",
    section: "Automation",
    level: "Intermediate",
    title: "Automations",
    summary: "Describe scheduled or triggered work such as reminders, reports, and cleanup tasks.",
    concepts: ["automation", "schedule", "task", "workflow", "cron-style jobs"],
    outcomes: [
      "Understand automations as background work.",
      "Describe recurring tasks in NovaDev source.",
      "Connect automations to workflows, routes, and backend modules.",
    ],
    explanation:
      "Automations are for work that should happen without a user clicking a button. Examples include sending daily reports, cleaning expired sessions, checking inventory, sending appointment reminders, or syncing external APIs.",
    code: `automation DailySalesReport {
    schedule every day at "08:00"
    task GenerateReport
    notify Admin
}

workflow GenerateReport {
    creates Report
    notify Manager
}

print("Daily automation declared")`,
    exercise: "Create an automation that sends a booking reminder every day at 09:00.",
    projectUse:
      "Use automations for reports, reminders, billing checks, inventory alerts, email queues, data imports, and scheduled cleanup.",
  },
  {
    id: "nova-math",
    section: "Standard Library",
    level: "Beginner",
    title: "Nova Math",
    summary: "Use math helpers for calculations beyond basic operators.",
    concepts: ["math", "round", "min", "max", "percent", "random"],
    outcomes: [
      "Use operators for simple calculations.",
      "Know when a math helper is clearer.",
      "Plan calculations for stores, dashboards, reports, and finance apps.",
    ],
    explanation:
      "NovaDev already supports arithmetic operators. A standard math module can add helper functions such as round, min, max, average, percent, clamp, and random. In generated Python backends, these map naturally to Python math and utility functions.",
    code: `let price = 29
let quantity = 3
let subtotal = price * quantity
let tax = subtotal * 0.15
let total = subtotal + tax

print("Subtotal: {subtotal}")
print("Tax: {tax}")
print("Total: {total}")`,
    exercise: "Write a function that calculates a 10 percent discount and returns the final total.",
    projectUse:
      "Use Nova math features for checkout totals, invoices, analytics, trading risk, school grades, finance dashboards, and reports.",
  },
  {
    id: "nova-dates-time",
    section: "Standard Library",
    level: "Intermediate",
    title: "Dates and Time",
    summary: "Represent dates for bookings, reports, logs, reminders, and scheduled jobs.",
    concepts: ["date", "time", "datetime", "formatting", "scheduling"],
    outcomes: [
      "Understand date fields in tables.",
      "Use dates in workflows and automations.",
      "Plan backend date handling with Python datetime.",
    ],
    explanation:
      "Many apps are time-based. Booking systems need appointment dates. Stores need order dates. Reports need ranges. Automations need schedules. NovaDev date declarations guide generated database fields and backend code.",
    code: `table Appointment {
    id auto
    customerName text
    service text
    appointmentDate date
    status text
}

automation AppointmentReminder {
    schedule every day at "09:00"
    notify Customer
}`,
    exercise: "Create a table named Event with title, startsAt, endsAt, and location.",
    projectUse:
      "Use dates and time in booking apps, hotel systems, event platforms, schools, invoices, reports, and task managers.",
  },
  {
    id: "nova-files-read-write",
    section: "Files and Storage",
    level: "Intermediate",
    title: "Reading and Writing Files",
    summary: "Use local file operations carefully in installed NovaDev projects.",
    concepts: ["read file", "write file", "append file", "local runtime", "permissions"],
    outcomes: [
      "Understand the difference between browser-safe code and local file access.",
      "Read text from a file in local/runtime projects.",
      "Write and append text when building tools and generators.",
    ],
    explanation:
      "File operations are powerful and should run only in trusted local projects or backend code. A website should not freely read or delete user files. NovaDev can document file actions and generate Python backend/runtime code that uses safe paths.",
    code: `module FileTools {
    function saveReport(path, text) {
        file.write(path, text)
    }

    function addLog(path, text) {
        file.append(path, text)
    }
}

print("File tools should run in local or backend mode")`,
    exercise: "Design a log writer that appends one line every time a workflow runs.",
    projectUse:
      "Use file operations for logs, exports, generated reports, uploads, local package files, templates, and project scaffolding.",
  },
  {
    id: "nova-files-delete",
    section: "Files and Storage",
    level: "Advanced",
    title: "Deleting Files Safely",
    summary: "Learn the safe pattern for delete operations in local tools and backends.",
    concepts: ["delete file", "safe paths", "uploads", "cleanup", "security"],
    outcomes: [
      "Understand why delete is dangerous.",
      "Restrict file deletion to known folders.",
      "Plan cleanup jobs without risking user data.",
    ],
    explanation:
      "Delete operations must be restricted. A safe generated backend should only delete inside an intended folder such as uploads, cache, or temp. It should not accept arbitrary paths from the internet.",
    code: `automation CleanupUploads {
    schedule every day at "02:00"
    task DeleteExpiredUploads
}

custom backend "services/cleanup.py" """
from pathlib import Path

UPLOADS = Path("uploads").resolve()

def safe_delete_upload(filename):
    target = (UPLOADS / filename).resolve()
    if UPLOADS not in target.parents:
        raise RuntimeError("unsafe delete path")
    target.unlink(missing_ok=True)
"""

print("Cleanup automation declared")`,
    exercise: "Write a rule that only deletes files from a cache folder.",
    projectUse:
      "Use safe delete patterns for upload cleanup, cache cleanup, old export files, temporary build output, and package-manager downloads.",
  },
  {
    id: "nova-sqlite",
    section: "Files and Storage",
    level: "Intermediate",
    title: "Nova SQLite",
    summary: "Use SQLite for local database-backed apps and generated Flask projects.",
    concepts: ["SQLite", "database", "CRUD", "queries", "SQLAlchemy"],
    outcomes: [
      "Understand SQLite as a file-based database.",
      "Connect table declarations to generated models.",
      "Use backend routes for create, read, update, and delete behavior.",
    ],
    explanation:
      "SQLite stores data in a local database file. NovaDev table declarations describe the data, while generated Flask and SQLAlchemy code can create models and routes that read and write records.",
    code: `app LibraryManager {
    project {
        frontend Vue
        backend Flask
        database SQLite
        styling Tailwind
        mode custom
    }

    table Book {
        id auto
        title text
        author text
        year number
    }

    route GET "/api/books" {
        return "books"
    }
}`,
    exercise: "Add POST, PUT, and DELETE routes for Book records.",
    projectUse:
      "Use Nova SQLite for admin tools, inventory apps, CRMs, school trackers, booking systems, local dashboards, and prototypes that need real persistence.",
  },
  {
    id: "nova-json",
    section: "Standard Library",
    level: "Intermediate",
    title: "JSON and Data Exchange",
    summary: "Use JSON-shaped data when frontends, backends, and APIs communicate.",
    concepts: ["JSON", "objects", "lists", "API responses", "serialization"],
    outcomes: [
      "Understand objects and lists as JSON-friendly data.",
      "Plan API responses.",
      "Use JSON for generated backend/frontend communication.",
    ],
    explanation:
      "Most modern APIs send JSON. NovaDev objects and lists map naturally to JSON structures. Generated Flask routes can return JSON, and Vue frontends can render that data.",
    code: `let product = {
    name: "Honeycrisp Box",
    price: 29,
    stock: 12
}

print(product.name)
print(product.price)`,
    exercise: "Create an object that represents an API response with status and data fields.",
    projectUse:
      "Use JSON for API responses, config files, package manifests, dashboards, external integrations, and generated frontend state.",
  },
  {
    id: "nova-http",
    section: "Standard Library",
    level: "Advanced",
    title: "HTTP and API Clients",
    summary: "Design backend service modules that call external HTTP APIs.",
    concepts: ["HTTP", "GET", "POST", "headers", "API clients"],
    outcomes: [
      "Understand frontend-to-backend-to-service flow.",
      "Use backend code for API clients.",
      "Keep headers and secrets out of the browser.",
    ],
    explanation:
      "NovaDev route declarations describe your API. Custom backend modules can call external APIs using Python libraries. This keeps tokens, API keys, and private headers on the server.",
    code: `custom backend "services/http_client.py" """
import os
import urllib.request

def get_json(url):
    request = urllib.request.Request(url)
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8")
"""

route GET "/api/external-status" {
    return "status"
}`,
    exercise: "Create a backend service that calls a shipping API without exposing the API key.",
    projectUse:
      "Use HTTP clients for payments, AI, email, maps, shipping, calendars, analytics, and external business systems.",
  },
  {
    id: "nova-cli-shell",
    section: "Developer Tools",
    level: "Beginner",
    title: "CLI and Shell Workflow",
    summary: "Use NovaDev through the command line, interactive shell, and online IDE.",
    concepts: ["nova", "shell", "run", "tokens", "ast", "build-ui"],
    outcomes: [
      "Know what nova.py commands do.",
      "Use the shell for quick experiments.",
      "Use tokens and AST to understand language behavior.",
    ],
    explanation:
      "NovaDev can be used like a normal local language: run files, open a shell, inspect tokens, inspect AST output, and build UI. The online IDE mirrors the most important learning commands.",
    code: `print("Commands to try locally:")
print("nova shell")
print("nova run examples/hello.nova")
print("nova tokens examples/hello.nova")
print("nova ast examples/hello.nova")
print("nova build-ui examples/business_admin.nova")`,
    exercise: "Run one file locally, then inspect its tokens and AST.",
    projectUse:
      "Use the CLI for real projects, CI scripts, package-manager checks, generated builds, and debugging language behavior.",
  },
  {
    id: "nova-security",
    section: "Professional Development",
    level: "Advanced",
    title: "Security Basics",
    summary: "Build NovaDev projects with safer defaults for secrets, files, routes, and generated code.",
    concepts: ["secrets", "validation", "safe paths", "auth", "least privilege"],
    outcomes: [
      "Keep API keys in environment variables.",
      "Validate route input before using it.",
      "Restrict file operations to safe folders.",
    ],
    explanation:
      "A real language ecosystem needs security habits. Secrets should live in environment variables. Backend routes should validate input. File operations should use safe paths. Generated auth should protect admin routes and workflows.",
    code: `auth {
    role Admin
    role Customer
}

page AdminDashboard {
    title "Admin"
    require role Admin
}

custom backend "services/secrets.py" """
import os

def require_secret(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is missing")
    return value
"""`,
    exercise: "Write a security checklist for a project that uses uploads and an API key.",
    projectUse:
      "Use these habits in every generated project: e-commerce, finance, healthcare, school, booking, delivery, CRM, and custom business tools.",
  },
];

export const examples = lessons;
export const starterCode = lessons[0].code;
