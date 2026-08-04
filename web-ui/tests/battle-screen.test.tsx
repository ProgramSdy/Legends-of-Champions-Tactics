import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { BattleScreen } from "@/components/battle/BattleScreen";
import { MockBattleProvider } from "@/lib/battle/fixture";

const demoDefinitions = [
  ["magic", "Magic attack"], ["healing", "Healing"], ["melee", "Melee"],
  ["status", "Apply status"], ["evade", "Evade"], ["summon", "Summon"],
] as const;

async function renderBattle(provider: MockBattleProvider = new MockBattleProvider()) {
  render(
    <BattleScreen
      provider={provider}
      mockDemos={demoDefinitions.map(([id, label]) => ({ id, label, run: () => provider.runDemo(id) }))}
    />,
  );
  await screen.findByRole("main");
  await screen.findByRole("complementary", { name: "Your team" });
  return provider;
}

describe("battle screen integration", () => {
  it("renders core landmarks, active hero, battle log, and accessible controls", async () => {
    await renderBattle();
    expect(screen.getByRole("complementary", { name: "Your team" })).toBeVisible();
    expect(screen.getByRole("complementary", { name: "Enemy team" })).toBeVisible();
    expect(screen.getByRole("region", { name: "Battlefield" })).toBeVisible();
    expect(screen.getByRole("navigation", { name: "Turn order" })).toBeVisible();
    expect(screen.getByRole("button", { name: "Settings" })).toBeEnabled();
    expect(screen.getByRole("link", { name: "Open asset gallery" })).toHaveAttribute("href", "/assets");
    expect(screen.getByRole("article", { name: /Arthas, Necromancer · Necromancer, active hero/i })).toHaveClass("active");
    expect(screen.queryByText("Choose a demo or select a skill.")).not.toBeInTheDocument();
  });

  it("selects a skill using keyboard interaction and exposes valid targets", async () => {
    const user = userEvent.setup();
    await renderBattle();
    const skill = screen.getByRole("button", { name: /Life Drain/i });
    skill.focus();
    await user.keyboard("{Enter}");
    expect(skill).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: "Sashein, selectable target" })).toHaveClass("target-selection-pending");
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeDisabled();
  });

  it("uses a crosshair only while required targets remain, including across both teams", async () => {
    const snapshot = (await new MockBattleProvider().getState()).snapshot;
    const lifeDrain = snapshot.legalActions.find((action) => action.skillId === "skill.life_drain")!;
    lifeDrain.minimumTargets = 2;
    lifeDrain.maximumTargets = 2;
    lifeDrain.validTargetIds = ["friendly.black_heart", "enemy.sashein", "enemy.andonidas"];
    const provider = new MockBattleProvider(snapshot);
    await renderBattle(provider);

    fireEvent.click(screen.getByRole("button", { name: /Life Drain/i }));
    const friendlyTarget = screen.getByRole("button", { name: "Black Heart, selectable target" });
    const enemyTarget = screen.getByRole("button", { name: "Sashein, selectable target" });
    const source = screen.getByRole("button", { name: "Arthas" });
    expect(friendlyTarget).toHaveClass("target-selection-pending");
    expect(enemyTarget).toHaveClass("target-selection-pending");
    expect(source).not.toHaveClass("target-selection-pending");

    fireEvent.click(friendlyTarget);
    expect(friendlyTarget).toHaveClass("target-selection-pending");

    fireEvent.click(enemyTarget);
    expect(friendlyTarget).not.toHaveClass("target-selection-pending");
    expect(enemyTarget).not.toHaveClass("target-selection-pending");
  });

  it("keeps selected-target state without rendering the legacy TARGET rectangle", async () => {
    const snapshot = (await new MockBattleProvider().getState()).snapshot;
    const lifeDrain = snapshot.legalActions.find((action) => action.skillId === "skill.life_drain")!;
    lifeDrain.minimumTargets = 2;
    lifeDrain.maximumTargets = 2;
    lifeDrain.validTargetIds = ["friendly.black_heart", "enemy.sashein", "enemy.andonidas"];
    await renderBattle(new MockBattleProvider(snapshot));

    fireEvent.click(screen.getByRole("button", { name: /Life Drain/i }));
    const friendlyTarget = screen.getByRole("button", { name: "Black Heart, selectable target" });
    fireEvent.click(friendlyTarget);
    expect(friendlyTarget.closest(".battle-figure")).toHaveClass("targeted");
    expect(friendlyTarget.closest(".battle-figure")).not.toHaveTextContent("TARGET");

    const css = readFileSync("app/globals.css", "utf8").replace(/\s+/g, "");
    expect(css).toMatch(/\.battle-figure\.targeted\{?[^}]*filter:drop-shadow/);
    expect(css).not.toMatch(/\.battle-figure\.targeted::after/);
    expect(css).not.toMatch(/content:\"TARGET\"/);
  });

  it("submits a structured useSkill command with revision, actor, skill, and selected targets", async () => {
    const provider = new MockBattleProvider();
    const submit = vi.spyOn(provider, "submitCommand");
    await renderBattle(provider);

    fireEvent.click(screen.getByRole("button", { name: /Life Drain/i }));
    fireEvent.click(screen.getByRole("button", { name: "Andonidas, selectable target" }));
    fireEvent.click(screen.getByRole("button", { name: "CAST SKILL" }));

    expect(submit).toHaveBeenCalledOnce();
    expect(submit).toHaveBeenCalledWith({
      type: "useSkill",
      commandId: expect.stringMatching(/^cmd\.[0-9a-f-]+$/),
      expectedRevision: 1,
      actorId: "friendly.arthas",
      skillId: "skill.life_drain",
      targetIds: ["enemy.andonidas"],
    });
  });

  it("keeps command submission usable when crypto.randomUUID is unavailable", async () => {
    const provider = new MockBattleProvider();
    const submit = vi.spyOn(provider, "submitCommand");
    const originalCrypto = globalThis.crypto;
    vi.stubGlobal("crypto", {});
    try {
      await renderBattle(provider);
      fireEvent.click(screen.getByRole("button", { name: /Life Drain/i }));
      fireEvent.click(screen.getByRole("button", { name: "Andonidas, selectable target" }));
      fireEvent.click(screen.getByRole("button", { name: "CAST SKILL" }));

      expect(submit).toHaveBeenCalledOnce();
      expect(submit.mock.calls[0][0]).toMatchObject({
        type: "useSkill",
        targetIds: ["enemy.andonidas"],
        commandId: expect.stringMatching(/^cmd\.[A-Za-z0-9-]+$/),
      });
    } finally {
      vi.unstubAllGlobals();
      vi.stubGlobal("crypto", originalCrypto);
    }
  });

  it("renders ordered battle-log messages and allows clearing them", async () => {
    await renderBattle();
    const log = screen.getByRole("list", { name: "Battle events" });
    Object.defineProperty(log, "scrollHeight", { configurable: true, value: 480 });
    const hpBefore = screen.getAllByText("49/76").length;
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "Evade" }));
    expect(await screen.findByText("Black Heart launches Shadow Bolt.")).toBeVisible();
    expect(await screen.findByText("Andonidas evades Shadow Bolt.")).toBeVisible();
    await waitFor(() => expect(log.scrollTop).toBe(480));
    expect(screen.getAllByText("49/76")).toHaveLength(hpBefore);
    fireEvent.click(screen.getByRole("button", { name: "Clear" }));
    expect(screen.queryByText("Choose a demo or select a skill.")).not.toBeInTheDocument();
  });

  it("keeps battlefield status interaction separate from target selection", async () => {
    const user = userEvent.setup();
    await renderBattle();
    await user.click(screen.getByRole("button", { name: /Life Drain/i }));
    const target = screen.getByRole("button", { name: "Sashein, selectable target" });
    const status = target.closest(".battle-figure")!.querySelector<HTMLElement>(".status-icon")!;

    expect(target).not.toContainElement(status);
    expect(status).toHaveAccessibleName(/Stitch of Agony.*2 rounds remaining/i);
    status.focus();
    await user.keyboard("{Enter} ");
    expect(status).toHaveFocus();
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeDisabled();

    target.focus();
    await user.keyboard("{Enter}");
    expect(screen.getByRole("button", { name: "CAST SKILL" })).toBeEnabled();
  });

  it("plays supplied events in sequence and reconciles HP presentation", async () => {
    await renderBattle();
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "Magic attack" }));
    const cast = await screen.findByText("Arthas casts Life Drain on Sashein.");
    const projectile = await screen.findByText("Necrotic energy arcs toward Sashein.");
    const damage = await screen.findByText("Sashein takes 18 magic damage.");
    const healing = await screen.findByText("Life Drain restores 12 health to Arthas.");
    expect(cast.compareDocumentPosition(projectile) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(projectile.compareDocumentPosition(damage) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(damage.compareDocumentPosition(healing) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect((await screen.findAllByText("45/81")).length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("73/81").length).toBeGreaterThanOrEqual(2);
  });

  it("changes presentation speed without changing battle authority", async () => {
    await renderBattle();
    const normal = screen.getByRole("button", { name: "×1" });
    const fast = screen.getByRole("button", { name: "×2" });
    expect(normal).toHaveClass("selected");
    fireEvent.click(fast);
    expect(fast).toHaveClass("selected");
    expect(normal).not.toHaveClass("selected");
    expect(screen.getByText(/Python remains gameplay authority/i)).toBeVisible();
  });

  it("inserts a supplied summon into the team panel, battlefield, and turn order", async () => {
    await renderBattle();
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "Summon" }));
    expect(await screen.findByText("Flesh Puppet joins the friendly team.")).toBeVisible();
    expect(await screen.findByRole("article", { name: /Flesh Puppet, Warrior/i })).toBeVisible();
    expect(screen.getAllByText("Flesh Puppet").length).toBeGreaterThanOrEqual(2);
  });

  it("renders floating damage from the active event amount", async () => {
    await renderBattle();
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "Melee" }));
    expect(await screen.findByText("−22")).toHaveClass("combat-text", "damage");
    expect(screen.queryByText("−18")).not.toBeInTheDocument();
  });

  it("skip followed by immediate replay cannot interleave or stale-reconcile", async () => {
    await renderBattle();
    fireEvent.click(screen.getByRole("button", { name: "×2" }));
    fireEvent.click(screen.getByRole("button", { name: "Magic attack" }));
    const skip = await screen.findByRole("button", { name: "SKIP EFFECT" });
    const log = screen.getByRole("list", { name: "Battle events" });
    Object.defineProperty(log, "scrollHeight", { configurable: true, value: 720 });
    fireEvent.click(skip);
    expect(await screen.findByText("Life Drain restores 12 health to Arthas.")).toBeVisible();
    await waitFor(() => expect(log.scrollTop).toBe(720));
    fireEvent.click(screen.getByRole("button", { name: "Summon" }));

    expect(await screen.findByText("Flesh Puppet joins the friendly team.")).toBeVisible();
    await waitFor(() => expect(screen.getByRole("article", { name: /Flesh Puppet, Warrior/i })).toBeVisible());
    await new Promise((resolve) => window.setTimeout(resolve, 700));
    expect(screen.getAllByText("45/81").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("73/81").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByRole("article", { name: /Flesh Puppet, Warrior/i })).toBeVisible();
  });

  it("preserves prior HP, summon, and refreshed status across sequential demos", async () => {
    await renderBattle();
    fireEvent.click(screen.getByRole("button", { name: "×2" }));

    fireEvent.click(screen.getByRole("button", { name: "Magic attack" }));
    await screen.findByText("Life Drain restores 12 health to Arthas.");
    await waitFor(() => expect(screen.getByRole("button", { name: "Summon" })).toBeEnabled());

    fireEvent.click(screen.getByRole("button", { name: "Summon" }));
    await screen.findByText("Flesh Puppet joins the friendly team.");
    await waitFor(() => expect(screen.getByRole("button", { name: "Apply status" })).toBeEnabled());

    fireEvent.click(screen.getByRole("button", { name: "Apply status" }));
    await screen.findByText("Stitch of Agony afflicts Sashein for 3 rounds.");
    await waitFor(() => expect(screen.getByRole("button", { name: "Magic attack" })).toBeEnabled());

    expect(screen.getAllByText("45/81").length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText("73/81").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByRole("article", { name: /Flesh Puppet, Warrior/i })).toBeVisible();
    expect(screen.getAllByLabelText(/Stitch of Agony.*3 rounds remaining/i).length).toBeGreaterThanOrEqual(2);
    expect(screen.queryByLabelText(/Stitch of Agony.*2 rounds remaining/i)).not.toBeInTheDocument();
  });

  it.each([[1920, 1080], [1600, 900], [1440, 900], [1366, 768]])(
    "keeps battle regions mounted at %d×%d",
    async (width, height) => {
      Object.defineProperty(window, "innerWidth", { configurable: true, value: width });
      Object.defineProperty(window, "innerHeight", { configurable: true, value: height });
      window.dispatchEvent(new Event("resize"));
      await renderBattle();
      expect(screen.getByRole("region", { name: "Battlefield" })).toBeInTheDocument();
      expect(screen.getByLabelText("Skills")).toBeInTheDocument();
      expect(document.querySelector(".battle-controls")).toBeInTheDocument();
    },
  );
});
