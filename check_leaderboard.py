#!/usr/bin/env python
"""Check leaderboard data."""

from services.rating_service import build_leaderboard
from app import create_app

app = create_app()

with app.app_context():
    from models import db
    data = build_leaderboard(db.session)
    
    print("=" * 50)
    print("LEADERBOARD DATA")
    print("=" * 50)
    print(f"\n📊 Total managers: {len(data)}")
    
    print(f"\n🏆 Top 10:")
    for i, m in enumerate(data[:10]):
        print(f"   {i+1}. {m['display_name']} - {m['total']} pts (rank={m['rank']})")
    
    print(f"\n📋 All managers:")
    for i, m in enumerate(data):
        print(f"   {i+1}. {m['display_name']} - {m['total']} pts")
    
    print("=" * 50)
