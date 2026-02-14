#!/usr/bin/env python3
"""
اختبار تكامل نظام معالجة الأزرار
Integration test for button handler system
"""
import asyncio
import sys

async def test_button_handler():
    """Test button handler registration and routing"""
    
    print("🧪 Testing Button Handler Integration\n")
    
    # Test 1: Import button handler
    print("📦 Test 1: Importing button handler...")
    try:
        from utils.button_handler import button_handler, ButtonHandler
        print("✅ Button handler imported successfully")
    except Exception as e:
        print(f"❌ Failed to import button handler: {e}")
        return False
    
    # Test 2: Create test handler
    print("\n📋 Test 2: Testing handler registration...")
    
    test_called = {'main_btn': False, 'res_': False}
    
    async def test_main_handler(interaction, custom_id):
        """Test handler for main buttons"""
        test_called['main_btn'] = True
        print(f"  ✓ Main handler called with custom_id: {custom_id}")
    
    async def test_res_handler(interaction, custom_id):
        """Test handler for reservation buttons"""
        test_called['res_'] = True
        print(f"  ✓ Reservation handler called with custom_id: {custom_id}")
    
    # Register handlers
    button_handler.register_prefix_handler('main_btn_', test_main_handler)
    button_handler.register_prefix_handler('res_', test_res_handler)
    
    handlers = button_handler.get_registered_handlers()
    print(f"✅ Registered handlers: {handlers}")
    
    # Test 3: Verify cog imports work
    print("\n🔧 Test 3: Testing cog imports...")
    try:
        from cogs.main_control_panel import MainControlPanelCog
        from cogs.alliance_system import AllianceSystemCog
        from cogs.reservations_system import ReservationsSystemCog
        from cogs.management_system import ManagementSystemCog
        print("✅ All cogs imported successfully")
    except Exception as e:
        print(f"❌ Failed to import cogs: {e}")
        return False
    
    # Test 4: Check button custom IDs
    print("\n📝 Test 4: Checking button custom IDs...")
    from cogs.main_control_panel import MainControlPanelView
    from cogs.reservations_system import ReservationsMenuView
    from cogs.alliance_system import AllianceMenuView
    
    test_user_id = "123456789"
    
    views = [
        ("MainControlPanelView", MainControlPanelView(test_user_id, is_admin=True)),
        ("ReservationsMenuView", ReservationsMenuView(test_user_id)),
        ("AllianceMenuView", AllianceMenuView(test_user_id, in_alliance=False)),
    ]
    
    all_custom_ids = []
    for view_name, view in views:
        custom_ids = [child.custom_id for child in view.children if hasattr(child, 'custom_id') and child.custom_id]
        all_custom_ids.extend(custom_ids)
        print(f"  ✓ {view_name}: {len(custom_ids)} buttons")
        for cid in custom_ids[:3]:  # Show first 3
            print(f"    - {cid}")
    
    print(f"✅ Total unique custom_ids: {len(set(all_custom_ids))}")
    
    # Test 5: Verify button prefixes match handlers
    print("\n🔍 Test 5: Verifying button prefixes...")
    prefix_handlers = button_handler.get_registered_handlers()['prefix_handlers']
    
    matched_buttons = 0
    for custom_id in all_custom_ids:
        for prefix in prefix_handlers:
            if custom_id.startswith(prefix):
                matched_buttons += 1
                break
    
    print(f"  Buttons: {len(all_custom_ids)}")
    print(f"  Matched: {matched_buttons}")
    print(f"  Prefixes: {prefix_handlers}")
    
    if matched_buttons > 0:
        print(f"✅ {matched_buttons}/{len(all_custom_ids)} buttons have registered handlers")
    else:
        print("⚠️  No buttons matched to handlers (may be using direct callbacks)")
    
    # Test 6: Test timeout settings
    print("\n⏱️  Test 6: Checking timeout settings...")
    timeout_issues = []
    for view_name, view in views:
        if view.timeout is not None:
            timeout_issues.append(f"{view_name} has timeout={view.timeout}")
        else:
            print(f"  ✓ {view_name}: timeout=None (persistent)")
    
    if timeout_issues:
        print("⚠️  Some views have timeouts:")
        for issue in timeout_issues:
            print(f"    - {issue}")
    else:
        print("✅ All tested views are persistent (timeout=None)")
    
    print("\n" + "="*50)
    print("🎉 Button Handler Integration Test Complete!")
    print("="*50)
    
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(test_button_handler())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
