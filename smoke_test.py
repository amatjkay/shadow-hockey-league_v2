"""Quick smoke test for Shadow Hockey League app."""
import sys
from app import create_app

def test_endpoints():
    app = create_app()
    with app.test_client() as client:
        results = []
        
        # Main page
        r = client.get('/')
        results.append(('GET /', r.status_code, 200))
        
        # Health check
        r = client.get('/health')
        results.append(('GET /health', r.status_code, 200))
        
        # Metrics
        r = client.get('/metrics')
        results.append(('GET /metrics', r.status_code, 200))
        
        # Admin (should work - either 200 or redirect)
        r = client.get('/admin/', follow_redirects=False)
        results.append(('GET /admin/', r.status_code, [200, 302, 301, 308]))
        
        # Admin login (Flask-Admin uses different routing)
        r = client.get('/admin/login/', follow_redirects=False)
        results.append(('GET /admin/login/', r.status_code, [200, 302, 301, 308]))
        
        # Print results
        print("\n=== ENDPOINT TEST RESULTS ===")
        all_pass = True
        for name, actual, expected in results:
            # expected can be a list
            if isinstance(expected, list):
                status = 'PASS' if actual in expected else 'FAIL'
            else:
                status = 'PASS' if actual == expected else 'FAIL'
            if status == 'FAIL':
                all_pass = False
            print(f'{status}: {name} -> {actual} (expected {expected})')
        
        print(f"\n{'ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'}")
        return all_pass

if __name__ == '__main__':
    success = test_endpoints()
    sys.exit(0 if success else 1)
