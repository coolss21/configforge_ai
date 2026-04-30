import asyncio
import json
import time
from app.compiler.pipeline import CompilerPipeline

async def run_test(name, prompt, expected_type, should_have_payments, should_have_premium, should_have_analytics):
    print(f"\n{'='*50}\nRunning {name}\nPrompt: {prompt}\n{'='*50}")
    p = CompilerPipeline()
    start = time.time()
    res = await p.generate(prompt, "fast")
    duration = time.time() - start
    
    report = res.get("validation_report", {})
    final_config = res.get("final_config", {})
    intent = final_config.get("intent", {})
    tables = [t["name"] for t in final_config.get("database", {}).get("tables", [])]
    features = [f.lower() for f in intent.get("features", [])]
    app_type = intent.get("app_type", "")
    is_valid = report.get("is_valid", False)
    
    print(f"App Type: {app_type} (Expected roughly: {expected_type})")
    print(f"Features: {features}")
    print(f"Tables: {tables}")
    print(f"Valid: {is_valid}")
    print(f"Executable: {res.get('runtime_report', {}).get('executable', False)}")
    print(f"Checks: {report.get('checks_count', 0)}")
    
    if report.get("errors"):
        print("ERRORS:")
        for err in report.get("errors"):
            print(f"  - {err.get('code')}: {err.get('message')}")
            
    # Quick checks
    assert should_have_payments == ("payments" in tables), f"Payments mismatch. Expected {should_have_payments}, got {'payments' in tables}"
    assert should_have_premium == ("plans" in tables or "subscriptions" in tables), f"Premium mismatch. Expected {should_have_premium}"
    assert is_valid, "Output is NOT valid!"

async def main():
    tests = [
        ("Test 1 (CRM)", "Build a CRM with login, contacts, dashboard, role-based access, premium plan with payments, and admin analytics.", "CRM", True, True, True),
        ("Test 2 (LMS)", "Build a learning management system with students, courses, assignments, submissions, and teacher dashboard.", "LMS", False, False, False),
        ("Test 3 (Hospital)", "Build a hospital appointment booking app with doctors, patients, appointment slots, payments, and admin dashboard.", "Healthcare Booking", True, False, False),
        ("Test 4 (Inventory)", "Build an inventory management app with suppliers, products, stock alerts, and staff roles.", "Inventory", False, False, False),
        ("Test 5 (Helpdesk)", "Build a helpdesk app with tickets, agents, customers, SLA rules, priority levels, and analytics.", "Helpdesk", False, False, True),
        ("Test 6 (Generic)", "Build me an app.", "Generic Internal Tool", False, False, False),
        ("Test 7 (Banking)", "Build a secure banking app with no auth.", "Generic Internal Tool", False, False, False)
    ]
    
    for t in tests:
        await run_test(*t)
        
if __name__ == "__main__":
    asyncio.run(main())
