"""
Unit Tests for Profit Taking Manager
=====================================

Tests for aggressive profit taking with partial exits.
"""

import pytest
from unittest.mock import Mock
from src.core.risk.profit_taking import (
    ProfitTakingManager,
    ProfitExitPlan,
    ProfitCheckResult,
    ProfitLevel
)
from src.data.database.models import Position


class TestProfitTakingManagerInitialization:
    """Test ProfitTakingManager initialization"""
    
    def test_initialization_loads_settings(self):
        """Test that initialization loads settings"""
        manager = ProfitTakingManager()
        
        assert manager.profit_level_1 == 0.05  # 5%
        assert manager.profit_level_2 == 0.10  # 10%
        assert manager.profit_level_3 == 0.20  # 20%
        assert manager.partial_exit_enabled is True
        assert manager.partial_exit_level_1_pct == 0.25  # 25%
        assert manager.partial_exit_level_2_pct == 0.50  # 50%


class TestProfitExitPlanCreation:
    """Test profit exit plan creation"""
    
    @pytest.fixture
    def manager(self):
        """Create profit taking manager"""
        return ProfitTakingManager()
    
    def test_create_exit_plan_default_levels(self, manager):
        """Test creating exit plan with default levels"""
        plan = manager.create_exit_plan(
            entry_price=100.0,
            quantity=100
        )
        
        assert plan.entry_price == 100.0
        assert plan.level_1_price == 105.0  # 5% profit
        assert plan.level_2_price == 110.0  # 10% profit
        assert plan.level_3_price == 120.0  # 20% profit
        assert plan.level_1_exit_pct == 0.25  # 25%
        assert plan.level_2_exit_pct == 0.50  # 50%
        assert plan.level_3_exit_pct == 0.25  # Remaining (100% - 25% - 50%)
        assert len(plan.levels_hit) == 0
    
    def test_create_exit_plan_custom_levels(self, manager):
        """Test creating exit plan with custom levels"""
        plan = manager.create_exit_plan(
            entry_price=100.0,
            quantity=100,
            custom_levels=(0.03, 0.08, 0.15)  # 3%, 8%, 15%
        )
        
        assert plan.level_1_price == 103.0  # 3% profit
        assert plan.level_2_price == 108.0  # 8% profit
        assert plan.level_3_price == 115.0  # 15% profit
    
    def test_create_exit_plan_custom_exit_percentages(self, manager):
        """Test creating exit plan with custom exit percentages"""
        plan = manager.create_exit_plan(
            entry_price=100.0,
            quantity=100,
            custom_exit_pcts=(0.30, 0.40)  # 30% at level 1, 40% at level 2
        )
        
        assert plan.level_1_exit_pct == 0.30
        assert plan.level_2_exit_pct == 0.40
        assert plan.level_3_exit_pct == 0.30  # Remaining (100% - 30% - 40%)


class TestProfitLevelChecking:
    """Test profit level checking logic"""
    
    @pytest.fixture
    def manager(self):
        """Create profit taking manager"""
        return ProfitTakingManager()
    
    @pytest.fixture
    def exit_plan(self):
        """Create sample exit plan"""
        manager = ProfitTakingManager()
        return manager.create_exit_plan(entry_price=100.0, quantity=100)
    
    def test_check_level_1_hit(self, manager, exit_plan):
        """Test detecting level 1 (5% profit)"""
        result = manager.check_profit_levels(
            current_price=105.0,  # Exactly at level 1
            exit_plan=exit_plan,
            current_quantity=100
        )
        
        assert result.should_exit is True
        assert result.profit_level == ProfitLevel.LEVEL_1
        assert result.exit_quantity == 25  # 25% of 100
        assert result.remaining_shares == 75
        assert ProfitLevel.LEVEL_1 in exit_plan.levels_hit
    
    def test_check_level_2_hit(self, manager, exit_plan):
        """Test detecting level 2 (10% profit)"""
        result = manager.check_profit_levels(
            current_price=110.0,  # Exactly at level 2
            exit_plan=exit_plan,
            current_quantity=100
        )
        
        assert result.should_exit is True
        assert result.profit_level == ProfitLevel.LEVEL_2
        assert result.exit_quantity == 50  # 50% of 100
        assert result.remaining_shares == 50
        assert ProfitLevel.LEVEL_2 in exit_plan.levels_hit
    
    def test_check_level_3_hit(self, manager, exit_plan):
        """Test detecting level 3 (20% profit)"""
        result = manager.check_profit_levels(
            current_price=120.0,  # Exactly at level 3
            exit_plan=exit_plan,
            current_quantity=100
        )
        
        assert result.should_exit is True
        assert result.profit_level == ProfitLevel.LEVEL_3
        assert result.exit_quantity == 100  # Exit remaining (all)
        assert result.remaining_shares == 0
        assert ProfitLevel.LEVEL_3 in exit_plan.levels_hit
    
    def test_check_no_level_hit(self, manager, exit_plan):
        """Test when no profit level is reached"""
        result = manager.check_profit_levels(
            current_price=102.0,  # Only 2% profit
            exit_plan=exit_plan,
            current_quantity=100
        )
        
        assert result.should_exit is False
        assert result.exit_quantity == 0
        assert result.remaining_shares == 100
        assert len(exit_plan.levels_hit) == 0
    
    def test_check_levels_sequential(self, manager, exit_plan):
        """Test sequential level hits"""
        # First hit level 1
        result1 = manager.check_profit_levels(
            current_price=105.0,
            exit_plan=exit_plan,
            current_quantity=100
        )
        assert result1.profit_level == ProfitLevel.LEVEL_1
        assert result1.exit_quantity == 25  # 25% of 100
        assert result1.remaining_shares == 75
        
        # Then hit level 2 (with remaining 75 shares)
        # Note: The implementation uses current_quantity * exit_pct for each level
        # So level 2 with 75 shares would be 50% of 75 = 37.5 -> 37 shares
        result2 = manager.check_profit_levels(
            current_price=110.0,
            exit_plan=exit_plan,
            current_quantity=75  # Remaining after level 1
        )
        assert result2.profit_level == ProfitLevel.LEVEL_2
        assert result2.exit_quantity == 37  # 50% of 75 (rounded down)
        assert result2.remaining_shares == 38
    
    def test_check_level_3_exits_all_remaining(self, manager, exit_plan):
        """Test that level 3 exits all remaining shares"""
        # Hit level 3 with some shares already sold
        result = manager.check_profit_levels(
            current_price=120.0,
            exit_plan=exit_plan,
            current_quantity=50  # Some already sold
        )
        
        assert result.exit_quantity == 50  # Exit all remaining
        assert result.remaining_shares == 0
    
    def test_check_zero_quantity(self, manager, exit_plan):
        """Test checking with zero quantity"""
        result = manager.check_profit_levels(
            current_price=110.0,
            exit_plan=exit_plan,
            current_quantity=0
        )
        
        assert result.should_exit is False
        assert result.exit_quantity == 0


class TestPartialExitDisabled:
    """Test profit taking with partial exit disabled"""
    
    @pytest.fixture
    def manager_no_partial(self):
        """Create manager with partial exit disabled"""
        manager = ProfitTakingManager()
        manager.partial_exit_enabled = False
        return manager
    
    def test_full_exit_at_level_1(self, manager_no_partial):
        """Test full exit at level 1 when partial exit disabled"""
        plan = manager_no_partial.create_exit_plan(entry_price=100.0, quantity=100)
        
        result = manager_no_partial.check_profit_levels(
            current_price=105.0,
            exit_plan=plan,
            current_quantity=100
        )
        
        assert result.exit_quantity == 100  # Full exit
        assert result.remaining_shares == 0


class TestProfitCalculation:
    """Test profit percentage calculation"""
    
    @pytest.fixture
    def manager(self):
        """Create profit taking manager"""
        return ProfitTakingManager()
    
    def test_get_profit_pct_positive(self, manager):
        """Test profit percentage calculation for profit"""
        profit_pct = manager.get_profit_pct(entry_price=100.0, current_price=105.0)
        
        assert abs(profit_pct - 0.05) < 0.001  # 5% profit
    
    def test_get_profit_pct_loss(self, manager):
        """Test profit percentage calculation for loss"""
        profit_pct = manager.get_profit_pct(entry_price=100.0, current_price=95.0)
        
        assert abs(profit_pct - (-0.05)) < 0.001  # -5% (loss)
    
    def test_get_profit_pct_zero_entry(self, manager):
        """Test profit percentage with zero entry price"""
        profit_pct = manager.get_profit_pct(entry_price=0.0, current_price=100.0)
        
        assert profit_pct == 0.0
    
    def test_get_profit_level_prices(self, manager):
        """Test getting profit level prices"""
        level_1, level_2, level_3 = manager.get_profit_level_prices(entry_price=100.0)
        
        assert level_1 == 105.0  # 5%
        assert level_2 == 110.0  # 10%
        assert level_3 == 120.0  # 20%
    
    def test_get_profit_level_prices_custom(self, manager):
        """Test getting profit level prices with custom levels"""
        level_1, level_2, level_3 = manager.get_profit_level_prices(
            entry_price=100.0,
            custom_levels=(0.03, 0.08, 0.15)
        )
        
        assert level_1 == 103.0  # 3%
        assert level_2 == 108.0  # 8%
        assert level_3 == 115.0  # 15%


class TestPositionIntegration:
    """Test profit taking with Position model"""
    
    @pytest.fixture
    def manager(self):
        """Create profit taking manager"""
        return ProfitTakingManager()
    
    @pytest.fixture
    def sample_position(self):
        """Create sample Position model"""
        from datetime import datetime
        position = Mock(spec=Position)
        position.average_price = 100.0
        position.quantity = 100
        return position
    
    def test_check_profit_for_position(self, manager, sample_position):
        """Test checking profit for a Position model"""
        result = manager.check_profit_for_position(
            position=sample_position,
            current_price=105.0
        )
        
        assert result.should_exit is True
        assert result.profit_level == ProfitLevel.LEVEL_1
    
    def test_check_profit_for_position_with_exit_plan(self, manager, sample_position):
        """Test checking profit with provided exit plan"""
        exit_plan = manager.create_exit_plan(entry_price=100.0, quantity=100)
        
        result = manager.check_profit_for_position(
            position=sample_position,
            current_price=110.0,
            exit_plan=exit_plan
        )
        
        assert result.profit_level == ProfitLevel.LEVEL_2


@pytest.mark.unit
class TestProfitTakingEdgeCases:
    """Test edge cases for profit taking"""
    
    @pytest.fixture
    def manager(self):
        """Create profit taking manager"""
        return ProfitTakingManager()
    
    def test_check_levels_price_between_levels(self, manager):
        """Test price between levels"""
        plan = manager.create_exit_plan(entry_price=100.0, quantity=100)
        
        # Price between level 1 and 2
        result = manager.check_profit_levels(
            current_price=107.0,  # 7% profit (between 5% and 10%)
            exit_plan=plan,
            current_quantity=100
        )
        
        # Should hit level 1 (first threshold crossed)
        assert result.profit_level == ProfitLevel.LEVEL_1
    
    def test_check_levels_price_above_all_levels(self, manager):
        """Test price above all levels"""
        plan = manager.create_exit_plan(entry_price=100.0, quantity=100)
        
        # Price way above level 3 (checks from highest to lowest)
        # At 150.0 (50% profit), should hit level 3 first
        result = manager.check_profit_levels(
            current_price=150.0,  # 50% profit
            exit_plan=plan,
            current_quantity=100
        )
        
        # Should hit level 3 (highest level reached first)
        assert result.profit_level == ProfitLevel.LEVEL_3
        assert result.exit_quantity == 100  # Exit all at level 3
        assert result.remaining_shares == 0
    
    def test_check_levels_not_hitting_levels_twice(self, manager):
        """Test that levels aren't hit twice"""
        plan = manager.create_exit_plan(entry_price=100.0, quantity=100)
        
        # Hit level 1
        result1 = manager.check_profit_levels(
            current_price=105.0,
            exit_plan=plan,
            current_quantity=100
        )
        assert result1.profit_level == ProfitLevel.LEVEL_1
        
        # Check again at same price (should not trigger again)
        result2 = manager.check_profit_levels(
            current_price=105.0,
            exit_plan=plan,
            current_quantity=75  # Remaining shares
        )
        assert result2.should_exit is False  # Already hit this level

