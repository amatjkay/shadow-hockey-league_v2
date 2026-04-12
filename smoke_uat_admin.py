"""Smoke UAT for admin flow: login → dashboard → API → logout."""
import sys
from app import create_app
from models import db, AdminUser, Manager, Country, Achievement

def smoke_uat_admin():
    """Test complete admin user flow."""
    app = create_app()
    
    with app.app_context():
        # Create test admin if not exists
        admin = AdminUser.query.filter_by(username='test_smoke').first()
        if not admin:
            admin = AdminUser(username='test_smoke')
            admin.set_password('test123')
            admin.role = 'admin'
            db.session.add(admin)
            db.session.commit()
            print("✅ Created test admin user")
        
        # Create test manager if not exists
        country = Country.query.filter_by(code='RUS').first()
        if not country:
            country = Country(code='RUS', name='Russia', flag_path='/static/img/flags/RUS.png')
            db.session.add(country)
            db.session.commit()
        
        manager = Manager.query.filter_by(name='Smoke Test Manager').first()
        if not manager:
            manager = Manager(name='Smoke Test Manager', country_id=country.id)
            db.session.add(manager)
            db.session.commit()
            print("✅ Created test manager")
    
    with app.test_client() as client:
        results = []
        
        # 1. Login page loads
        r = client.get('/admin/login/')
        results.append(('GET /admin/login/', r.status_code, 200))
        print(f"1. Login page: {r.status_code}")
        
        # 2. Login
        r = client.post('/admin/login/', data={
            'username': 'test_smoke',
            'password': 'test123'
        }, follow_redirects=False)
        results.append(('POST /admin/login/', r.status_code, [302, 303]))
        print(f"2. Login POST: {r.status_code}")
        
        # Follow redirect to dashboard
        if r.status_code in [302, 303]:
            r = client.get(r.location)
            results.append(('GET /admin/ (dashboard)', r.status_code, 200))
            print(f"3. Dashboard: {r.status_code}")
            
            # Check for BuildError (P0-1)
            if b'BuildError' in r.data:
                results.append(('Dashboard BuildError check', 'FAIL', 'PASS'))
                print("❌ Dashboard has BuildError!")
            else:
                results.append(('Dashboard BuildError check', 'PASS', 'PASS'))
                print("✅ Dashboard loads without BuildError")
        else:
            results.append(('GET /admin/ (dashboard)', 'SKIP', 200))
        
        # 4. API: Get manager achievements (P0-2)
        # Reload manager ID in test client context to avoid DetachedInstanceError
        with app.app_context():
            manager_id = Manager.query.filter_by(name='Smoke Test Manager').first().id
        
        r = client.get(f'/admin/api/managers/{manager_id}/achievements')
        results.append((f'GET /admin/api/managers/{manager_id}/achievements', r.status_code, 200))
        print(f"4. Manager achievements API: {r.status_code}")
        
        # 5. Logout (P0-3)
        r = client.get('/admin/logout/', follow_redirects=False)
        results.append(('GET /admin/logout/', r.status_code, [302, 303]))
        print(f"5. Logout: {r.status_code}")
        
        # Follow redirect to login
        if r.status_code in [302, 303]:
            r = client.get(r.location)
            results.append(('GET redirect after logout', r.status_code, 200))
            print(f"6. After logout redirect: {r.status_code}")
            
            # Check for BuildError in logout (P0-3)
            if b'BuildError' in r.data:
                results.append(('Logout BuildError check', 'FAIL', 'PASS'))
                print("❌ Logout has BuildError!")
            else:
                results.append(('Logout BuildError check', 'PASS', 'PASS'))
                print("✅ Logout works without BuildError")
        else:
            results.append(('GET redirect after logout', 'SKIP', 200))
        
        # Print results
        print("\n=== SMOKE UAT RESULTS ===")
        all_pass = True
        for name, actual, expected in results:
            if isinstance(expected, list):
                status = 'PASS' if actual in expected else 'FAIL'
            else:
                status = 'PASS' if actual == expected else 'FAIL'
            if status == 'FAIL':
                all_pass = False
            print(f'{status}: {name} -> {actual} (expected {expected})')
        
        print(f"\n{'ALL SMOKE UAT PASSED' if all_pass else 'SOME SMOKE UAT FAILED'}")
        return all_pass

if __name__ == '__main__':
    success = smoke_uat_admin()
    sys.exit(0 if success else 1)
