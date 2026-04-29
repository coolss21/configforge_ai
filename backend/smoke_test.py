import asyncio, sys
sys.path.insert(0, '.')

SAMPLE_CONFIG = {
    'intent': {
        'app_name':'CRM','app_type':'CRM','description':'crm with login',
        'primary_users':['user'],'features':['login'],'entities':[
            {'name':'contact','description':'A contact','fields':[
                {'name':'email','type':'email','required':True,'description':'Email'}
            ]}
        ],
        'roles':['admin','user'],'permissions':[],'business_rules':[],
        'integrations':[],'ambiguities':[],'assumptions':[]
    },
    'database': {'tables':[
        {'name':'contacts','fields':[
            {'name':'id',  'type':'INTEGER','primary_key':True, 'nullable':False,'unique':True},
            {'name':'name','type':'TEXT',   'primary_key':False,'nullable':False,'unique':False}
            # email intentionally MISSING
        ]}
    ]},
    'api': {'endpoints':[
        {'path':'/api/contacts','method':'GET','entity':'contacts',
         'operation':'list','required_role':'user','request_body':{},'response_body':{}}
    ]},
    'ui': {'pages':[
        {'name':'Dash','route':'/dashboard','layout':'dashboard','required_role':None,'components':[
            {'type':'data_table','entity':'contacts','api_endpoint':'/api/contacts','fields':['name']}
        ]}
    ]},
    'auth': {
        'auth_required': True,
        'roles': [{'name':'user','permissions':['read']}],  # admin MISSING
        'access_rules': [],                                  # empty intentionally
        'auth_rules_validated': True
    },
    'business_logic': {'rules':[]},
    'runtime_report': {}
}


async def main():
    # ── Test 1: Validator ─────────────────────────────────────────────────────
    from app.compiler.validators.master_validator import MasterValidator
    v = MasterValidator()
    r = v.validate(SAMPLE_CONFIG)
    print('=== VALIDATION REPORT ===')
    print(f'  valid         : {r["is_valid"]}')
    print(f'  error_count   : {r["error_count"]}')
    print(f'  warning_count : {r["warning_count"]}')
    print(f'  checks_count  : {r["checks_count"]}')
    print(f'  time_ms       : {r["validation_time_ms"]}')
    for e in r['errors']:
        print(f'  [{e["code"]}] {e["message"][:80]}')

    # ── Test 2: Repair engine ─────────────────────────────────────────────────
    print('\n=== REPAIR ENGINE ===')
    import copy
    from app.compiler.repair.repair_engine import RepairEngine
    repaired = await RepairEngine().run(copy.deepcopy(SAMPLE_CONFIG), 'fast')
    rr = repaired['repair_report']
    vr = repaired['validation_report']
    print(f'  repair_rounds    : {rr["repair_rounds"]}')
    print(f'  repaired_layers  : {rr["repaired_layers"]}')
    print(f'  repair_time_ms   : {rr["repair_time_ms"]}')
    print(f'  after valid      : {vr["is_valid"]}')
    if vr['errors']:
        for e in vr['errors']:
            print(f'  UNRESOLVED [{e["code"]}] {e["message"][:80]}')
    auth_after = repaired.get('auth', {})
    print(f'  auth roles       : {[r["name"] for r in auth_after.get("roles",[])]}')
    print(f'  access_rules cnt : {len(auth_after.get("access_rules",[]))}')
    db_after = repaired.get('database', {})
    for t in db_after.get('tables', []):
        if t['name'] == 'contacts':
            print(f'  contacts fields  : {[f["name"] for f in t["fields"]]}')

    # ── Test 3: Executor full CRUD ────────────────────────────────────────────
    print('\n=== EXECUTOR (FULL CRUD) ===')
    from app.compiler.runtime.executor import Executor
    report = Executor().execute(repaired)
    print(f'  executable       : {report["executable"]}')
    print(f'  tables_created   : {report["tables_created"]}')
    print(f'  auth_rules_valid : {report["auth_rules_validated"]}')
    print(f'  api_routes cnt   : {len(report["api_routes_registered"])}')
    print(f'  simulation count : {len(report["simulation_results"])}')
    for s in report['simulation_results']:
        status = 'OK  ' if s['success'] else 'FAIL'
        print(f'    [{status}] {s["operation"]:45s} {s["message"]}')
    if report['errors']:
        for e in report['errors']:
            print(f'  ERROR: {e}')

    # ── Test 4: Debug-repair endpoint logic (inline) ──────────────────────────
    print('\n=== DEBUG REPAIR CASES ===')
    from app.compiler.validators.master_validator import MasterValidator
    mv = MasterValidator()
    broken_auth = copy.deepcopy(SAMPLE_CONFIG)
    pre  = mv.validate(broken_auth)
    fix  = await RepairEngine().run(broken_auth, 'fast')
    post = fix['validation_report']
    print(f'  Before: {[e["code"] for e in pre["errors"]]}')
    print(f'  After : {[e["code"] for e in post["errors"]]}')
    print(f'  Repaired layers: {fix["repair_report"]["repaired_layers"]}')

    # ── Test 5: Full pipeline offline ────────────────────────────────────────
    print('\n=== PIPELINE (OFFLINE/FALLBACK) ===')
    from app.compiler.pipeline import CompilerPipeline
    result = await CompilerPipeline().generate(
        'CRM with login, contacts, dashboard, role-based access, admin and user roles.', 'fast'
    )
    m = result['metrics']
    rr2 = result['runtime_report']
    print(f'  success          : {result["success"]}')
    print(f'  latency_ms       : {m["latency_ms"]}')
    print(f'  checks_count     : {m["checks_count"]}')
    print(f'  error_count      : {m["error_count"]}')
    print(f'  warning_count    : {m["warning_count"]}')
    print(f'  validation_ms    : {m["validation_time_ms"]}')
    print(f'  simulation_count : {m["simulation_count"]}')
    print(f'  executable       : {rr2["executable"]}')
    print(f'  tables_created   : {rr2["tables_created"]}')
    api_routes = rr2.get("api_routes_registered", [])
    print(f'  api_routes ({len(api_routes)}): {api_routes[:5]}{"..." if len(api_routes)>5 else ""}')
    print(f'  auth_rules_valid : {rr2["auth_rules_validated"]}')
    auth_roles = [r["name"] for r in result["final_config"].get("auth",{}).get("roles",[])]
    print(f'  auth_roles       : {auth_roles}')
    rules_cnt = len(result["final_config"].get("auth",{}).get("access_rules",[]))
    print(f'  access_rules cnt : {rules_cnt}')
    from_cache = result.get('_from_cache', False)
    print(f'  from_cache       : {from_cache}')
    # Second call should be cached
    result2 = await CompilerPipeline().generate(
        'CRM with login, contacts, dashboard, role-based access, admin and user roles.', 'fast'
    )
    print(f'  second call cache: {result2.get("_from_cache", False)}')

asyncio.run(main())
