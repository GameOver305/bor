#!/usr/bin/env python3
"""
Test database robustness improvements
Verify that database operations work even if directory/file is deleted during runtime
"""
import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DatabaseManager


async def test_database_robustness():
    """Test that database recovers from file/directory deletion"""
    
    print("=" * 60)
    print("Testing Database Robustness")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = os.path.join(tmpdir, "test_subdir", "test.db")
        print(f"\nTest database path: {test_db_path}")
        
        # Test 1: Initialize database
        print("\n✅ Test 1: Initialize database")
        db_manager = DatabaseManager(db_path=test_db_path)
        await db_manager.initialize()
        assert os.path.exists(test_db_path), "Database file should exist"
        print("✅ Database initialized")
        
        # Test 2: Create a user and verify it works
        print("\n✅ Test 2: Create user")
        user = await db_manager.get_or_create_user(
            discord_id="123456789",
            username="TestUser",
            player_id="P123"
        )
        assert user is not None, "User should be created"
        print(f"✅ User created: {user.username}")
        
        # Test 3: Delete the database file (simulating runtime deletion)
        print("\n✅ Test 3: Delete database file (simulating runtime deletion)")
        os.remove(test_db_path)
        assert not os.path.exists(test_db_path), "Database file should be deleted"
        print("✅ Database file deleted")
        
        # Test 4: Try to query - should auto-recover
        print("\n✅ Test 4: Auto-recovery after deletion")
        user2 = await db_manager.get_or_create_user(
            discord_id="987654321",
            username="TestUser2",
            player_id="P456"
        )
        assert user2 is not None, "User should be created after recovery"
        assert os.path.exists(test_db_path), "Database file should be recreated"
        print(f"✅ Database auto-recovered, new user created: {user2.username}")
        
        # Test 5: Delete entire directory (simulating more severe issue)
        print("\n✅ Test 5: Delete entire database directory")
        shutil.rmtree(os.path.dirname(test_db_path))
        assert not os.path.exists(os.path.dirname(test_db_path)), "Directory should be deleted"
        print("✅ Database directory deleted")
        
        # Test 6: Try to query - should auto-recover
        print("\n✅ Test 6: Auto-recovery after directory deletion")
        user3 = await db_manager.get_or_create_user(
            discord_id="111222333",
            username="TestUser3",
            player_id="P789"
        )
        assert user3 is not None, "User should be created after recovery"
        assert os.path.exists(test_db_path), "Database file should be recreated"
        assert os.path.exists(os.path.dirname(test_db_path)), "Directory should be recreated"
        print(f"✅ Database and directory auto-recovered, new user created: {user3.username}")
        
        # Test 7: Verify other operations work
        print("\n✅ Test 7: Verify other operations work after recovery")
        result = await db_manager.fetchone("SELECT COUNT(*) FROM users")
        user_count = result[0] if result else 0
        # After directory deletion, the database was recreated from scratch.
        # Previous users (user1, user2) were lost because the entire database file
        # was deleted. Only user3 exists because it was created after the recovery.
        assert user_count == 1, f"Expected 1 user after recovery, found {user_count}"
        print(f"✅ Query works: found {user_count} user(s) as expected")
        
        # Test 8: Test with multiple rapid operations
        print("\n✅ Test 8: Test multiple rapid operations")
        for i in range(5):
            user = await db_manager.get_or_create_user(
                discord_id=f"rapid{i}",
                username=f"RapidUser{i}",
                player_id=f"R{i}"
            )
            assert user is not None, f"User {i} should be created"
        print(f"✅ Created 5 users rapidly without issues")
        
    print("\n" + "=" * 60)
    print("✅ All robustness tests passed!")
    print("=" * 60)


async def test_concurrent_operations():
    """Test concurrent database operations"""
    
    print("\n" + "=" * 60)
    print("Testing Concurrent Database Operations")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = os.path.join(tmpdir, "concurrent_test.db")
        print(f"\nTest database path: {test_db_path}")
        
        db_manager = DatabaseManager(db_path=test_db_path)
        await db_manager.initialize()
        
        # Create multiple users concurrently
        print("\n✅ Creating 10 users concurrently")
        tasks = []
        for i in range(10):
            task = db_manager.get_or_create_user(
                discord_id=f"concurrent{i}",
                username=f"ConcurrentUser{i}",
                player_id=f"C{i}"
            )
            tasks.append(task)
        
        users = await asyncio.gather(*tasks)
        assert len(users) == 10, "All 10 users should be created"
        print(f"✅ Successfully created {len(users)} users concurrently")
        
        # Query all users concurrently
        print("\n✅ Querying users concurrently")
        query_tasks = [
            db_manager.get_user_by_discord_id(f"concurrent{i}")
            for i in range(10)
        ]
        queried_users = await asyncio.gather(*query_tasks)
        assert len(queried_users) == 10, "All 10 users should be queried"
        print(f"✅ Successfully queried {len(queried_users)} users concurrently")
        
    print("\n" + "=" * 60)
    print("✅ All concurrent operation tests passed!")
    print("=" * 60)


async def main():
    try:
        await test_database_robustness()
        await test_concurrent_operations()
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
