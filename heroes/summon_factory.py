# Summon factory to avoid circular imports from Mage and SummonUnit
from heroes.summon_unit import WaterElemental, SkeletonWarrior, SkeletonMage, VoidRambler

class SummonFactory:
    @staticmethod
    def create_summon(name, sys_init, group, master, duration, summon_unit_race, is_player_controlled=False):
        """
        Central factory to create summonable units without circular imports.
        """

        if name == "WaterElemental":
            return WaterElemental(sys_init, f"{master.name}'s Water Elemental", group, master, duration, summon_unit_race, is_player_controlled)

        elif name == "SkeletonWarrior":
            return SkeletonWarrior(sys_init, f"{master.name}'s Skeleton Warrior", group, master, duration, summon_unit_race, is_player_controlled)

        elif name == "SkeletonMage":
            return SkeletonMage(sys_init, f"{master.name}'s Skeleton Mage", group, master, duration, summon_unit_race, is_player_controlled)

        elif name == "VoidRambler":
            return VoidRambler(sys_init, f"{master.name}'s Void Rambler", group, master, duration, summon_unit_race, is_player_controlled)

        else:
            raise ValueError(f"Unknown summon type: {name}")