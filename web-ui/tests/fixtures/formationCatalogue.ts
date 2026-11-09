const ids = ["front-rear", "side-by-side", "one-front-two-rear", "two-front-one-rear", "all-front"] as const;
const types = ["melee", "rangedProjectile", "rangedInstant"] as const;

export function createFormationCatalogue() {
  return {
    contractVersion: "1.0",
    attackTypes: [...types],
    formations: ids.map((id) => {
      const size = id === "front-rear" || id === "side-by-side" ? 2 : 3;
      const positions = id === "front-rear" ? ["front", "rear"] : id === "one-front-two-rear" ? ["front", "rear", "rear"] : id === "two-front-one-rear" ? ["front", "front", "rear"] : Array(size).fill("front");
      const friendlySlots = positions.map((position, index) => ({ slot: index + 1, position }));
      const enemySlots = positions.map((position, index) => ({ slot: index + 1, position }));
      const evaluations = friendlySlots.flatMap((attacker) => types.flatMap((attackType) => [false, ...(positions.includes("rear") ? [true] : [])].map((enemyFrontDefeated) => ({
        attackerSlot: attacker.slot,
        attackerPosition: attacker.position,
        attackType,
        enemyFrontDefeated,
        explanation: `${attacker.position} ${attackType} explanation`,
        targets: enemySlots.map((target) => {
          const defeated = enemyFrontDefeated && target.position === "front";
          const screened = attackType === "melee" && !enemyFrontDefeated && target.position === "rear";
          return {
            targetSlot: target.slot,
            targetPosition: target.position,
            eligible: !defeated && !screened,
            multiplierPercent: defeated || screened ? null : attackType === "melee" && attacker.position === "rear" ? 70 : attackType === "rangedProjectile" && attacker.position === "rear" && target.position === "rear" ? 60 : attackType === "rangedProjectile" && attacker.position !== target.position ? 80 : 100,
            reason: defeated ? "defeated" : screened ? "protectedByFrontLine" : "eligible",
          };
        }),
      }))));
      return { id, battleSize: size, hasRearEnemies: positions.includes("rear"), friendlySlots, enemySlots, evaluations };
    }),
  };
}
