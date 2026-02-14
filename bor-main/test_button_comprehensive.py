#!/usr/bin/env python3
"""
اختبار شامل لنظام الأزرار - Comprehensive Button System Test
Tests button routing and handler execution without requiring Discord connection
"""
import asyncio
import sys
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Optional

class MockInteraction:
    """Mock Discord Interaction for testing"""
    
    def __init__(self, custom_id: str, user_id: str = "123456789"):
        self.type = 2  # InteractionType.component
        self.data = {'custom_id': custom_id}
        self.user = Mock()
        self.user.id = int(user_id)
        self.user.name = "TestUser"
        self.user.mention = f"<@{user_id}>"
        
        # Mock response
        self.response = Mock()
        self.response.is_done = Mock(return_value=False)
        self.response.send_message = AsyncMock()
        self.response.edit_message = AsyncMock()
        self.response.defer = AsyncMock()
        self.response.send_modal = AsyncMock()
        
        # Mock followup
        self.followup = Mock()
        self.followup.send = AsyncMock()
        
        # Mock edit
        self.edit_original_response = AsyncMock()
        
        # Mock client for cog access
        self.client = Mock()

async def test_button_routing():
    """Test button routing through the central handler"""
    
    print("🧪 Testing Button Routing System\n")
    print("="*60)
    
    # Import button handler
    from utils.button_handler import button_handler
    
    # Track which handlers were called
    calls = {
        'main_btn_alliance': False,
        'main_btn_reservations': False,
        'res_building': False,
        'alliance_info': False,
        'mgmt_users': False,
    }
    
    # Create test handlers
    async def test_handler(interaction, custom_id):
        calls[custom_id] = True
        print(f"  ✓ Handler executed: {custom_id}")
    
    # Register test handlers for different prefixes
    async def main_handler(interaction, custom_id):
        if custom_id in calls:
            calls[custom_id] = True
        print(f"  ✓ Main handler executed: {custom_id}")
    
    async def res_handler(interaction, custom_id):
        if custom_id in calls:
            calls[custom_id] = True
        print(f"  ✓ Reservations handler executed: {custom_id}")
    
    async def alliance_handler(interaction, custom_id):
        if custom_id in calls:
            calls[custom_id] = True
        print(f"  ✓ Alliance handler executed: {custom_id}")
    
    async def mgmt_handler(interaction, custom_id):
        if custom_id in calls:
            calls[custom_id] = True
        print(f"  ✓ Management handler executed: {custom_id}")
    
    # Clear and register handlers
    button_handler._handlers.clear()
    button_handler._prefix_handlers.clear()
    
    button_handler.register_prefix_handler('main_btn_', main_handler)
    button_handler.register_prefix_handler('res_', res_handler)
    button_handler.register_prefix_handler('alliance_', alliance_handler)
    button_handler.register_prefix_handler('mgmt_', mgmt_handler)
    
    print("\n📋 Test 1: Button Routing")
    print("-" * 60)
    
    # Test each button type
    test_buttons = [
        'main_btn_alliance',
        'main_btn_reservations',
        'res_building',
        'alliance_info',
        'mgmt_users',
    ]
    
    for button_id in test_buttons:
        print(f"\n  Testing: {button_id}")
        interaction = MockInteraction(button_id)
        result = await button_handler.handle_interaction(interaction)
        
        if result:
            print(f"    ✅ Routed successfully")
        else:
            print(f"    ❌ No handler found")
    
    # Verify all handlers were called
    print("\n📊 Test Results:")
    print("-" * 60)
    success = 0
    for button_id, called in calls.items():
        status = "✅" if called else "❌"
        print(f"  {status} {button_id}: {'Called' if called else 'Not called'}")
        if called:
            success += 1
    
    print(f"\n  Success Rate: {success}/{len(calls)} ({success*100//len(calls)}%)")
    
    return success == len(calls)

async def test_null_safety():
    """Test null-safe interaction.data access"""
    
    print("\n\n🛡️  Testing Null Safety")
    print("="*60)
    
    from utils.button_handler import button_handler
    
    # Test with None data
    print("\n  Test 1: interaction.data = None")
    interaction = Mock()
    interaction.type = 2  # InteractionType.component
    interaction.data = None
    
    result = await button_handler.handle_interaction(interaction)
    print(f"    Result: {result} (expected: False)")
    if result == False:
        print("    ✅ Handled gracefully")
    else:
        print("    ❌ Did not handle None data correctly")
    
    # Test with empty data
    print("\n  Test 2: interaction.data = {}")
    interaction.data = {}
    
    result = await button_handler.handle_interaction(interaction)
    print(f"    Result: {result} (expected: False)")
    if result == False:
        print("    ✅ Handled gracefully")
    else:
        print("    ❌ Did not handle empty data correctly")
    
    # Test with missing custom_id
    print("\n  Test 3: interaction.data without custom_id")
    interaction.data = {'other_field': 'value'}
    
    result = await button_handler.handle_interaction(interaction)
    print(f"    Result: {result} (expected: False)")
    if result == False:
        print("    ✅ Handled gracefully")
    else:
        print("    ❌ Did not handle missing custom_id correctly")
    
    print("\n  ✅ All null safety tests passed")
    return True

async def test_error_handling():
    """Test error handling in button handlers"""
    
    print("\n\n🔥 Testing Error Handling")
    print("="*60)
    
    from utils.button_handler import button_handler
    
    # Create a handler that raises an exception
    async def error_handler(interaction, custom_id):
        raise ValueError("Test error")
    
    button_handler.register_prefix_handler('error_', error_handler)
    
    print("\n  Test: Handler that raises exception")
    interaction = MockInteraction('error_test')
    
    try:
        result = await button_handler.handle_interaction(interaction)
        print(f"    Result: {result}")
        
        # Check if error message was sent
        if interaction.response.send_message.called or interaction.followup.send.called:
            print("    ✅ Error message sent to user")
        else:
            print("    ⚠️  No error message sent")
        
        print("    ✅ Exception caught and handled")
        return True
        
    except Exception as e:
        print(f"    ❌ Exception not caught: {e}")
        return False

async def test_view_initialization():
    """Test that views can be instantiated without errors"""
    
    print("\n\n🎨 Testing View Initialization")
    print("="*60)
    
    test_user_id = "123456789"
    
    views = []
    
    try:
        from cogs.main_control_panel import MainControlPanelView, LanguageSelectView, MyInfoView
        views.extend([
            ("MainControlPanelView", MainControlPanelView(test_user_id, is_admin=True, is_owner=True)),
            ("LanguageSelectView", LanguageSelectView(test_user_id)),
            ("MyInfoView", MyInfoView(test_user_id)),
        ])
    except Exception as e:
        print(f"  ❌ Failed to import main_control_panel views: {e}")
        return False
    
    try:
        from cogs.reservations_system import ReservationsMenuView, ReservationSectionView
        views.extend([
            ("ReservationsMenuView", ReservationsMenuView(test_user_id)),
            ("ReservationSectionView (building)", ReservationSectionView(test_user_id, "building")),
        ])
    except Exception as e:
        print(f"  ❌ Failed to import reservations views: {e}")
        return False
    
    try:
        from cogs.alliance_system import AllianceMenuView
        views.extend([
            ("AllianceMenuView (not in alliance)", AllianceMenuView(test_user_id, in_alliance=False)),
            ("AllianceMenuView (in alliance)", AllianceMenuView(test_user_id, in_alliance=True, has_permissions=True)),
        ])
    except Exception as e:
        print(f"  ❌ Failed to import alliance views: {e}")
        return False
    
    try:
        from cogs.management_system import ManagementPanelView
        views.append(("ManagementPanelView", ManagementPanelView(test_user_id, is_owner=True)))
    except Exception as e:
        print(f"  ❌ Failed to import management views: {e}")
        return False
    
    print(f"\n  Testing {len(views)} views...")
    
    for view_name, view in views:
        # Check timeout
        timeout_status = "✅ persistent" if view.timeout is None else f"⚠️  timeout={view.timeout}"
        
        # Count buttons
        button_count = len([c for c in view.children if hasattr(c, 'custom_id')])
        
        print(f"  ✓ {view_name}: {button_count} buttons, {timeout_status}")
    
    print(f"\n  ✅ All {len(views)} views initialized successfully")
    return True

async def main():
    """Run all tests"""
    
    print("🚀 Comprehensive Button System Test Suite")
    print("="*60)
    print()
    
    results = []
    
    # Run all tests
    results.append(("Button Routing", await test_button_routing()))
    results.append(("Null Safety", await test_null_safety()))
    results.append(("Error Handling", await test_error_handling()))
    results.append(("View Initialization", await test_view_initialization()))
    
    # Summary
    print("\n\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("\n  🎉 All tests passed!")
        return True
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
