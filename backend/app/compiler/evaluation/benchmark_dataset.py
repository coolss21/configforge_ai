NORMAL_PROMPTS = [
    {"id": "n1", "type": "normal", "prompt": "CRM with login, contacts, dashboard, role-based access, premium plan, payments, admin analytics."},
    {"id": "n2", "type": "normal", "prompt": "Inventory management app with suppliers, products, stock alerts, staff roles."},
    {"id": "n3", "type": "normal", "prompt": "Learning management system with students, courses, assignments, teacher dashboard."},
    {"id": "n4", "type": "normal", "prompt": "Appointment booking app with customers, services, staff calendar, payments."},
    {"id": "n5", "type": "normal", "prompt": "Expense tracker with categories, budgets, reports, user authentication."},
    {"id": "n6", "type": "normal", "prompt": "Helpdesk ticketing app with agents, tickets, priorities, SLA rules."},
    {"id": "n7", "type": "normal", "prompt": "Job board with companies, candidates, job posts, applications, admin moderation."},
    {"id": "n8", "type": "normal", "prompt": "Restaurant ordering app with menu, cart, orders, delivery status, admin panel."},
    {"id": "n9", "type": "normal", "prompt": "Gym membership app with plans, trainers, attendance, payments."},
    {"id": "n10", "type": "normal", "prompt": "Project management app with teams, tasks, milestones, role permissions."}
]

EDGE_PROMPTS = [
    {"id": "e1", "type": "edge", "prompt": "Build me an app."},
    {"id": "e2", "type": "edge", "prompt": "Create something like Notion but for doctors."},
    {"id": "e3", "type": "edge", "prompt": "Build a CRM but no database."},
    {"id": "e4", "type": "edge", "prompt": "Make a public anonymous app where every page requires admin login."},
    {"id": "e5", "type": "edge", "prompt": "Build an ecommerce app with payments but no users."},
    {"id": "e6", "type": "edge", "prompt": "I need a dashboard for analytics but do not store any data."},
    {"id": "e7", "type": "edge", "prompt": "Make a school app with teachers and students and doctors and invoices."},
    {"id": "e8", "type": "edge", "prompt": "Build a SaaS app with premium plan but everything should be free."},
    {"id": "e9", "type": "edge", "prompt": "Create an app for managing stuff."},
    {"id": "e10", "type": "edge", "prompt": "Build a secure banking app with no auth."}
]

BENCHMARK_DATASET = NORMAL_PROMPTS + EDGE_PROMPTS
