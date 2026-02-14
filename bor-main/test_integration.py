#!/usr/bin/env python3
"""
Integration test for database fixes
Test that the bot can start and perform database operations
"""
import asyncio
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from database import db


async def test_integration():
    """Test the complete database integration"""
    
    print("=" * 60)
    print("Integration Test - Database Path Fixes")
    print("=" * 60)
    
    # Test 1: Paths are absolute
    print("\n✅ Test 1: Verify absolute paths")
    print(f"DATABASE_PATH: {config.DATABASE_PATH}")
    assert os.path.isabs(config.DATABASE_PATH), "DATABASE_PATH must be absolute"
    print("✅ Path is absolute")
    
    # Test 2: Database initialization (similar to bot startup)
    print("\n✅ Test 2: Database initialization")
    try:
        # Ensure directories exist (similar to bot.py main())
        os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
        os.makedirs(config.BACKUP_DIR, exist_ok=True)
        os.makedirs(config.LOGS_DIR, exist_ok=True)
        print("✅ Directories created")
        
        # Initialize database
        await db.initialize()
        print("✅ Database initialized")
        
        # Verify database file exists
        assert os.path.exists(config.DATABASE_PATH), f"Database file should exist at {config.DATABASE_PATH}"
        print(f"✅ Database file exists: {config.DATABASE_PATH}")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        raise
    
    # Test 3: Database operations
    print("\n✅ Test 3: Database operations")
    try:
        # Create a user
        user = await db.get_or_create_user(
            discord_id="987654321",
            username="IntegrationTestUser",
            player_id="P999"
        )
        print(f"✅ User created: {user.username} (ID: {user.user_id})")
        
        # Get user
        retrieved_user = await db.get_user_by_discord_id("987654321")
        assert retrieved_user is not None, "User should be retrievable"
        assert retrieved_user.username == "IntegrationTestUser"
        print("✅ User retrieval works")
        
        # Test stats
        stats = await db.get_stats()
        print(f"✅ Stats retrieved: {stats['total_users']} users")
        
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        raise
    
    # Test 4: Test from different working directory
    print("\n✅ Test 4: Working directory independence")
    original_cwd = os.getcwd()
    try:
        # Change to temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            print(f"Changed working directory to: {os.getcwd()}")
            
            # Database operations should still work with absolute paths
            user = await db.get_user_by_discord_id("987654321")
            assert user is not None, "Should work from any directory with absolute paths"
            print("✅ Database operations work from different directory")
            
    finally:
        os.chdir(original_cwd)
        print(f"Restored working directory to: {os.getcwd()}")
    
    print("\n" + "=" * 60)
    print("✅ All integration tests passed!")
    print("=" * 60)
    print("\nSummary:")
    print("- Absolute paths are working correctly")
    print("- Database initialization works")
    print("- Database operations work")
    print("- Working directory independence verified")


async def main():
    try:
        await test_integration()
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
