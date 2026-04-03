#!/usr/bin/env python
"""Check countries in database."""

from app import create_app
from models import db, Country

app = create_app()

with app.app_context():
    countries = db.session.query(Country).all()
    print("=" * 50)
    print("COUNTRIES IN DATABASE")
    print("=" * 50)
    
    for c in countries:
        status = "OK" if c.name != "Unknown" else "WARN"
        print(f"  [{status}] {c.code}: {c.name} ({c.flag_path})")
    
    print("=" * 50)
    
    # Check for any "Unknown" countries
    unknown = [c for c in countries if c.name == "Unknown"]
    if unknown:
        print(f"\nWARN - Found {len(unknown)} countries with 'Unknown' name:")
        for c in unknown:
            print(f"   - {c.code}")
    else:
        print(f"\nOK - All {len(countries)} countries have proper names!")
